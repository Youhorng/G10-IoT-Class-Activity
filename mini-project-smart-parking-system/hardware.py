# ── hardware.py
# Merges: ultrasonic, ir_sensor, servo, relay, dht_sensor, tm1637, lcd, clock 

from machine import Pin, PWM, I2C, time_pulse_us
from time    import sleep_us
import utime, dht as _dht, gc

# ═══════════════════════════════════════════════════════════════
#  ULTRASONIC — HC-SR04  TRIG=D5 ECHO=D18
# ═══════════════════════════════════════════════════════════════
class Ultrasonic:
    def __init__(self,trig,echo):
        self.t=Pin(trig,Pin.OUT); self.e=Pin(echo,Pin.IN)
        self.t.value(0); utime.sleep_ms(100)
    def distance(self):
        self.t.value(0); utime.sleep_us(2)
        self.t.value(1); utime.sleep_us(10); self.t.value(0)
        d=time_pulse_us(self.e,1,30000)
        return 999 if d<0 else (d*0.034)/2

# ═══════════════════════════════════════════════════════════════
#  IR SENSORS — slots D34,35,32,33,25 / exit D26
#  invert=False: 1=car  |  invert=True: 0=car (confirmed)
# ═══════════════════════════════════════════════════════════════
class IRSensor:
    def __init__(self,pins,invert=False):
        self.s=[Pin(p,Pin.IN) for p in pins]; self.inv=invert
        print("[IR] pins="+str(pins)+" raw=["+",".join(str(x.value()) for x in self.s)+"] inv="+str(invert))
    def _occ(self,v): return (v==1) if self.inv else (v==0)
    def update(self,state):
        for i,s in enumerate(self.s): state.slots[i]=self._occ(s.value())
    def read_one(self,i=0): return self._occ(self.s[i].value())
    #def read_one(self,i=0):
        #import utime
        #readings = [self._occ(self.s[i].value()) for _ in range(3)]
        #utime.sleep_ms(10)
        #return readings.count(True) >= 2

# ═══════════════════════════════════════════════════════════════
#  SERVO — entry D13 / exit D15 (NOT D12 — boot sensitive)
#  External 5V power — NOT ESP32 VIN (brownout risk)
#  Speed 300ms confirmed from standalone test
# ═══════════════════════════════════════════════════════════════
class Servo:
    def __init__(self,pin,open_deg=90,close_deg=0):
        self.pwm=PWM(Pin(pin),freq=50)
        self.od=open_deg; self.cd=close_deg
        self._go(close_deg); utime.sleep_ms(50); self.pwm.duty(0)
    def _go(self,d): self.pwm.duty(int(26+(d/180)*(128-26)))
    def open(self):  self._go(self.od);  utime.sleep_ms(50); self.pwm.duty(0)
    def close(self): self._go(self.cd);  utime.sleep_ms(50); self.pwm.duty(0)

# ═══════════════════════════════════════════════════════════════
#  RELAY — D2 active LOW  value(0)=ON value(1)=OFF
# ═══════════════════════════════════════════════════════════════
class Relay:
    def __init__(self,pin):
        self.p=Pin(pin,Pin.OUT); self.off()
    def on(self):   self.p.value(0)
    def off(self):  self.p.value(1)
    @property
    def is_on(self): return self.p.value()==0

# ═══════════════════════════════════════════════════════════════
#  DHT11 — D4  (file named hardware.py avoids dht name conflict)
# ═══════════════════════════════════════════════════════════════
class DHTSensor:
    def __init__(self,pin):
        self.s=_dht.DHT11(Pin(pin)); self._t=0.0; self._h=0.0
    def read(self):
        try:
            self.s.measure()
            self._t=float(self.s.temperature()); self._h=float(self.s.humidity())
        except OSError as e: print("[DHT] "+str(e))
        return self._t,self._h

# ═══════════════════════════════════════════════════════════════
#  TM1637 — slot display D14/D27 | clock display D19/D23
# ═══════════════════════════════════════════════════════════════
_SEG=[0x3F,0x06,0x5B,0x4F,0x66,0x6D,0x7D,0x07,0x7F,0x6F]

class TM1637:
    def __init__(self,clk_pin,dio_pin,brightness=7):
        self.c=Pin(clk_pin,Pin.OUT,value=1)
        self.d=Pin(dio_pin,Pin.OUT,value=1)
        self.br=brightness; self._upd()
    def _st(self):  self.d.value(0); sleep_us(10); self.c.value(0)
    def _sp(self):  self.c.value(1); sleep_us(10); self.d.value(1)
    def _wb(self,b):
        for _ in range(8):
            self.d.value(b&1); b>>=1
            self.c.value(1); sleep_us(10); self.c.value(0)
        self.c.value(1); sleep_us(10); self.c.value(0)
    def _upd(self):
        self._st(); self._wb(0x80|0x08|self.br); self._sp()
    def _send(self,data):
        self._st(); self._wb(0x40); self._sp()
        self._st(); self._wb(0xC0)
        for s in data: self._wb(s)
        self._sp(); self._upd()
        
    def show(self,available,total=5):
        if available==0:
        # Display "FULL" using segments F=0x71  U=0x3E  L=0x38  L=0x38
            self._send([0x71,0x3E,0x38,0x38])
        else:
            n=max(0,min(available,9999)); s=str(n)
            d=[0]*4
            for i,ch in enumerate(s): d[4-len(s)+i]=_SEG[int(ch)]
            self._send(d)
    def show_clock(self,h,m,colon=True):
        d=[_SEG[h//10],_SEG[h%10],_SEG[m//10],_SEG[m%10]]
        if colon: d[1]|=0x80
        self._send(d)

# ═══════════════════════════════════════════════════════════════
#  LCD I2C — SDA=D21 SCL=D22  addr=0x27 or 0x3F
# ═══════════════════════════════════════════════════════════════
class LCD:
    def __init__(self,sda,scl,addr=0x27):
        self.i=I2C(0,sda=Pin(sda),scl=Pin(scl),freq=400000)
        self.a=addr; self.bl=0x08; self._init()
    def _w(self,v):  self.i.writeto(self.a,bytes([v|self.bl]))
    def _en(self,v): self._w(v|0x04); utime.sleep_us(1); self._w(v&~0x04); utime.sleep_us(50)
    def _nb(self,n,m):
        d=(n<<4)|(m); self._w(d); self._en(d)
    def _by(self,b,m=1):
        self._nb((b>>4)&0xF,m); self._nb(b&0xF,m)
    def _cmd(self,c): self._by(c,0); utime.sleep_ms(1)
    def _init(self):
        utime.sleep_ms(50)
        for _ in range(3): self._nb(0x03,0); utime.sleep_ms(5)
        self._nb(0x02,0); utime.sleep_ms(1)
        self._cmd(0x28); self._cmd(0x0C); self._cmd(0x06); self.clear()
    def clear(self): self._cmd(0x01); utime.sleep_ms(2)
    def _cur(self,c,r): self._cmd(0x80|(c+[0x00,0x40][r]))
    def _wr(self,t):
        for ch in t: self._by(ord(ch),1)
    def write_line(self,row,text):
        self._cur(0,row); t=text[:16]; t=t+' '*(16-len(t)); self._wr(t)
    def show_message(self,l1,l2=""):
        self.write_line(0,str(l1)); self.write_line(1,str(l2))
    def update(self,st):
        l1,l2=st.lcd_lines(); self.write_line(0,l1); self.write_line(1,l2)

# ═══════════════════════════════════════════════════════════════
#  CLOCK — NTP UTC+7
# ═══════════════════════════════════════════════════════════════
_base_epoch=0; _base_ticks=0

def sync_ntp():
    global _base_epoch,_base_ticks
    try:
        import ntptime; gc.collect(); ntptime.settime()
        t=utime.localtime()
        _base_epoch=utime.mktime(t)+7*3600
        _base_ticks=utime.ticks_ms()
        h,m,s=get_hms()
        print("[CLOCK] Synced — {:02d}:{:02d}:{:02d} UTC+7".format(h,m,s))
    except Exception as e:
        print("[CLOCK] NTP failed: "+str(e))
        _base_epoch=7*3600; _base_ticks=utime.ticks_ms()
    finally: gc.collect()

def _now():
    return _base_epoch+utime.ticks_diff(utime.ticks_ms(),_base_ticks)//1000

def get_hms():
    t=utime.localtime(_now()); return t[3],t[4],t[5]

def get_time_str():
    h,m,s=get_hms(); return "{:02d}:{:02d}".format(h,m)

def get_full_str():
    h,m,s=get_hms(); return "{:02d}:{:02d}:{:02d}".format(h,m,s)

