# ── iot.py — Telegram + Web Server + Blynk in one file ────────
import urequests, ujson, socket, gc
from state import state
from config import BLYNK_V_SERVO, BLYNK_V_TEMP, BLYNK_V_SLOTS

# ═══════════════════════════════════════════════════════════════
#  TELEGRAM BOT
#  Commands: /status /open /close /slots /temp /light_on /light_off /help
# ═══════════════════════════════════════════════════════════════
class TelegramBot:
    def __init__(self,token,chat_id,entry_servo,relay):
        self.base="https://api.telegram.org/bot"+token
        self.cid=str(chat_id); self.sv=entry_servo
        self.rl=relay; self.offset=0

    def send(self,text):
        r=None
        try:
            gc.collect()
            r=urequests.post(self.base+"/sendMessage",
                headers={"Content-Type":"application/json"},
                data=ujson.dumps({"chat_id":self.cid,"text":text}))
        except Exception as e: print("[TG] send err:"+str(e))
        finally:
            try:
                if r: r.close()
            except: pass
            gc.collect()

    async def poll(self):
        r=None
        try:
            gc.collect()
            r=urequests.get(self.base+"/getUpdates?offset="+str(self.offset)+"&limit=1&timeout=0")
            raw=r.text; r.close(); r=None
            data=ujson.loads(raw); del raw; gc.collect()
            for u in data.get("result",[]):
                self.offset=u["update_id"]+1
                txt=u.get("message",{}).get("text","").strip().lower()
                if txt: self._cmd(txt)
            del data; gc.collect()
        except Exception as e: print("[TG] poll err:"+str(e))
        finally:
            try:
                if r: r.close()
            except: pass
            gc.collect()

    def _cmd(self,cmd):
        from logic import manual_open,manual_close,manual_light_on,manual_light_off
        cmd = cmd.split("@")[0]
        print("[TG] "+cmd)
        if   cmd=="/status":   self.send(state.summary())
        elif cmd=="/slots":
            lines=["Parking Slots:"]
            for i in range(state.total):
                lines.append("["+("X" if state.slots[i] else "O")+"] P"+str(i+1)+": "+state.slot_label(i))
            lines.append("Free: "+str(state.available)+"/"+str(state.total))
            self.send("\n".join(lines))
        elif cmd=="/open":      manual_open(self.sv); self.send("Entry gate opened.")
        elif cmd=="/close":     manual_close(self.sv); self.send("Entry gate closed.")
        elif cmd=="/temp":      self.send("Temp: "+str(state.temperature)+" C\nHumid: "+str(state.humidity)+" %")
        elif cmd=="/light_on":  manual_light_on(self.rl); self.send("Lights ON.")
        elif cmd=="/light_off": manual_light_off(self.rl); self.send("Lights OFF.")
        elif cmd=="/help":
            self.send("/status /open /close /slots /temp /light_on /light_off /help")
        else: self.send("Unknown. Type /help")

# ═══════════════════════════════════════════════════════════════
#  WEB SERVER — port 80, auto-refresh 3s
# ═══════════════════════════════════════════════════════════════
class WebServer:
    def __init__(self,entry_servo,exit_servo,relay,port=80):
        self.sv=entry_servo; self.xv=exit_servo; self.rl=relay
        self.sock=socket.socket(); self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind(('',port)); self.sock.listen(3); self.sock.setblocking(False)
        print("[WEB] port "+str(port))

    def _page(self):
        from hardware import get_full_str
        slots=""
        for i in range(state.total):
            c="occ" if state.slots[i] else "free"
            l="OCC" if state.slots[i] else "FREE"
            slots+='<div class="slot '+c+'"><b>P'+str(i+1)+'</b><br>'+l+'</div>'
        g="open" if state.gate_open else "closed"; gl="OPEN" if state.gate_open else "CLOSED"
        lo="lon" if state.light_on  else "loff";  ll="ON"   if state.light_on  else "OFF"
        fb='<span class="full">FULL</span>' if state.is_full else ""
        av=str(state.available)+"/"+str(state.total)
        try: ct=get_full_str()
        except: ct="--:--:--"
        return ("<!DOCTYPE html><html><head>"
            "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta http-equiv='refresh' content='3'><title>Smart Parking</title>"
            "<style>"
            "*{box-sizing:border-box;margin:0;padding:0}"
            "body{font-family:Arial,sans-serif;background:#0f172a;color:#e2e8f0;padding:14px}"
            "h1{text-align:center;color:#38bdf8;font-size:1.5rem;margin-bottom:4px}"
            ".sub{text-align:center;color:#64748b;font-size:.75rem;margin-bottom:18px}"
            ".card{background:#1e293b;border-radius:10px;padding:14px;margin-bottom:12px}"
            ".ct{font-size:.65rem;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:8px}"
            ".slots{display:flex;gap:6px;flex-wrap:wrap;justify-content:center}"
            ".slot{width:64px;padding:8px 4px;border-radius:8px;text-align:center;font-size:.75rem}"
            ".free{background:#14532d;color:#86efac}.occ{background:#7f1d1d;color:#fca5a5}"
            ".bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}"
            ".av{font-size:1.2rem;font-weight:bold;color:#38bdf8}"
            ".full{background:#ef4444;color:#fff;padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:bold}"
            ".grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}"
            ".gi{text-align:center}.gl{font-size:.65rem;color:#64748b}.gv{font-size:1.1rem;font-weight:bold;margin-top:2px}"
            ".open{color:#34d399}.closed{color:#f87171}.lon{color:#fbbf24}.loff{color:#94a3b8}"
            ".env{display:flex;gap:14px;justify-content:center;font-size:.95rem;flex-wrap:wrap}"
            ".env span{color:#94a3b8;font-size:.75rem}"
            ".time{text-align:center;font-size:1.3rem;font-weight:bold;color:#38bdf8;margin-top:6px}"
            ".btns{display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px}"
            "a.btn{display:block;padding:10px;border-radius:7px;text-align:center;font-weight:600;font-size:.82rem;text-decoration:none}"
            ".bg{background:#0ea5e9;color:#fff}.br{background:#6366f1;color:#fff}"
            ".by{background:#f59e0b;color:#000}.bs{background:#475569;color:#fff}"
            "footer{text-align:center;margin-top:14px;color:#334155;font-size:.65rem}"
            "</style></head><body>"
            "<h1>Smart Parking</h1><div class='sub'>Refreshes every 3s</div>"
            "<div class='card'><div class='ct'>Slots</div>"
            "<div class='bar'><div>Free: <span class='av'>"+av+"</span></div>"+fb+"</div>"
            "<div class='slots'>"+slots+"</div></div>"
            "<div class='card'><div class='ct'>Status</div><div class='grid'>"
            "<div class='gi'><div class='gl'>Gate</div><div class='gv "+g+"'>"+gl+"</div></div>"
            "<div class='gi'><div class='gl'>Lights</div><div class='gv "+lo+"'>"+ll+"</div></div>"
            "</div></div>"
            "<div class='card'><div class='ct'>Environment</div>"
            "<div class='env'>"
            "<div>"+str(state.temperature)+" C <span>Temp</span></div>"
            "<div>"+str(state.humidity)+"% <span>Humid</span></div>"
            "</div><div class='time'>"+ct+" <span style='font-size:.75rem;color:#94a3b8'>UTC+7</span></div></div>"
            "<div class='card'><div class='ct'>Controls</div><div class='btns'>"
            "<a class='btn bg' href='/?cmd=open'>Open Gate</a>"
            "<a class='btn br' href='/?cmd=close'>Close Gate</a>"
            "<a class='btn bg' href='/?cmd=openx'>Open Exit</a>"
            "<a class='btn br' href='/?cmd=closex'>Close Exit</a>"
            "<a class='btn by' href='/?cmd=lon'>Light ON</a>"
            "<a class='btn bs' href='/?cmd=loff'>Light OFF</a>"
            "</div></div>"
            "<footer>Smart IoT Parking | ESP32 MicroPython</footer>"
            "</body></html>")

    async def handle(self):
        try:
            from logic import manual_open,manual_close,manual_light_on,manual_light_off
            conn,_=self.sock.accept(); conn.settimeout(3.0)
            try: req=conn.recv(512).decode("utf-8","ignore")
            except: req=""
            if   "cmd=openx"  in req: manual_open(self.xv)
            elif "cmd=closex" in req: manual_close(self.xv)
            elif "cmd=open"   in req: manual_open(self.sv)
            elif "cmd=close"  in req: manual_close(self.sv)
            elif "cmd=lon"    in req: manual_light_on(self.rl)
            elif "cmd=loff"   in req: manual_light_off(self.rl)
            pg=self._page()
            conn.sendall("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: "+str(len(pg))+"\r\nConnection: close\r\n\r\n"+pg)
            conn.close()
        except OSError: pass
        except Exception as e: print("[WEB] "+str(e))

# ═══════════════════════════════════════════════════════════════
#  BLYNK — V0=gate button V1=temp V2=slots
# ═══════════════════════════════════════════════════════════════
class Blynk:
    def __init__(self,token,entry_servo,exit_servo):
        self.base="https://blynk.cloud/external/api"
        self.tk=token
        self.sv=entry_servo
        self.xv=exit_servo
        self._last_v0=None
        self._last_v4=None
        self._step=0

    def _get(self,pin):
        r=None
        try:
            gc.collect()
            r=urequests.get(self.base+"/get?token="+self.tk+"&"+pin)
            v=r.text.strip().strip('"')
            return v
        except Exception as e:
            print("[BLYNK] GET "+str(e))
            return None
        finally:
            try:
                if r: r.close()
            except: pass
            gc.collect()

    def _set(self,pin,value):
        r=None
        try:
            gc.collect()
            r=urequests.get(self.base+"/update?token="+self.tk+"&"+pin+"="+str(value))
        except Exception as e:
            print("[BLYNK] SET "+str(e))
        finally:
            try:
                if r: r.close()
            except: pass
            gc.collect()

    async def sync(self):
        from logic import manual_open,manual_close
        from config import BLYNK_V_SERVO,BLYNK_V_TEMP,BLYNK_V_SLOTS,BLYNK_V_HUM,BLYNK_V_EXIT

        # Push one value per cycle — rotates through 4 steps
        if   self._step==0: self._set(BLYNK_V_TEMP,  str(state.temperature))
        elif self._step==1: self._set(BLYNK_V_SLOTS, str(state.available))
        elif self._step==2: self._set(BLYNK_V_HUM,   str(state.humidity))
        # step 3 = read only, no push
        self._step=(self._step+1)%4

        # Read entry gate button V0
        v0=self._get(BLYNK_V_SERVO)
        if v0 is not None and v0!=self._last_v0:
            self._last_v0=v0
            if   v0=="1": manual_open(self.sv);  print("[BLYNK] entry gate open")
            elif v0=="0": manual_close(self.sv); print("[BLYNK] entry gate close")

        # Read exit gate button V4
        v4=self._get(BLYNK_V_EXIT)
        if v4 is not None and v4!=self._last_v4:
            self._last_v4=v4
            if   v4=="1": manual_open(self.xv);  print("[BLYNK] exit gate open")
            elif v4=="0": manual_close(self.xv); print("[BLYNK] exit gate close")
