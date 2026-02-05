import network
import socket
import time
from machine import Pin, I2C, time_pulse_us
import dht
from lcd_api import LcdApi
from machine_i2c_lcd import I2cLcd

# ================= WIFI =================
SSID = "AI WIFI"
PASSWORD = "AIetl@2025"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
while not wlan.isconnected():
    time.sleep(1)

ip = wlan.ifconfig()[0]
print("Connected:", wlan.ifconfig())
print("Open:", "http://%s/" % ip)

# ================= HARDWARE =================
led = Pin(2, Pin.OUT)
led.value(0)

dht_sensor = dht.DHT11(Pin(4))

trig = Pin(27, Pin.OUT)
echo = Pin(26, Pin.IN)

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = I2cLcd(i2c, 0x27, 2, 16)  # change to 0x3F if needed
lcd.clear()

# ================= SENSOR FUNCTIONS =================
def read_temp_c():
    try:
        dht_sensor.measure()
        return dht_sensor.temperature()
    except:
        return None

def read_distance_cm():
    try:
        trig.value(0)
        time.sleep_us(2)
        trig.value(1)
        time.sleep_us(10)
        trig.value(0)

        duration = time_pulse_us(echo, 1, 30000)  # 30ms timeout
        if duration < 0:
            return None

        dist = (duration * 0.0343) / 2
        return round(dist, 2)
    except:
        return None

# ================= LCD HELPERS =================
def lcd_write(line, text):
    lcd.move_to(0, line)
    lcd.putstr(" " * 16)
    lcd.move_to(0, line)
    lcd.putstr((text or "")[:16])

def lcd_scroll_repeat(line, text, delay=0.22, repeat=True, max_seconds=8):
    """
    Repeat scrolling if text > 16 chars.
    - repeat=True  -> loop forever (NOT recommended because server will freeze while scrolling)
    - max_seconds  -> set to None for truly infinite, or set seconds to stop scrolling automatically
    """
    if text is None:
        return
    text = str(text)

    # If short, just show it
    if len(text) <= 16:
        lcd_write(line, text)
        return

    # Marquee: add spacing and wrap
    gap = " " * 6
    padded = text + gap

    start = time.ticks_ms()
    i = 0
    L = len(padded)

    while True:
        # Stop if max_seconds is set and exceeded
        if max_seconds is not None:
            if time.ticks_diff(time.ticks_ms(), start) > (max_seconds * 1000):
                break

        # show a moving 16-char window (wrap around)
        window = ""
        for k in range(16):
            window += padded[(i + k) % L]

        lcd_write(line, window)
        time.sleep(delay)

        i = (i + 1) % L

        # If not repeating, exit after one full cycle
        if not repeat and i == 0:
            break

# ================= URL HELPERS =================
def url_decode(s):
    # safer minimal decode for common cases
    if not s:
        return ""
    s = s.replace("+", " ")
    s = s.replace("%20", " ")
    s = s.replace("%2C", ",").replace("%2E", ".").replace("%2D", "-").replace("%5F", "_")
    s = s.replace("%3A", ":").replace("%3F", "?").replace("%3D", "=").replace("%2F", "/")
    s = s.replace("%25", "%")
    return s

def get_query_value(path, key):
    if "?" not in path:
        return ""
    qs = path.split("?", 1)[1]
    for kv in qs.split("&"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            if k == key:
                return v
    return ""

# ================= PAGES / API =================
def html_page():
    return """HTTP/1.1 200 OK
Content-Type: text/html

<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ESP32 IoT Panel</title>
  <style>
    :root{
      --bg0:#070A12; --bg1:#0B1020;
      --card:rgba(255,255,255,.08); --card2:rgba(255,255,255,.06);
      --stroke:rgba(255,255,255,.12);
      --text:#EAF0FF; --muted:rgba(234,240,255,.65);
      --accent:#7C5CFF; --accent2:#22C55E;
      --warn:#F59E0B; --danger:#EF4444;
      --shadow: 0 20px 60px rgba(0,0,0,.45);
      --radius:18px;
    }
    *{ box-sizing:border-box; }
    body{
      margin:0; padding:18px; min-height:100vh;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      color:var(--text);
      background:
        radial-gradient(900px 500px at 15% 10%, rgba(124,92,255,.35), transparent 55%),
        radial-gradient(800px 480px at 85% 15%, rgba(34,197,94,.20), transparent 55%),
        radial-gradient(700px 500px at 45% 90%, rgba(245,158,11,.18), transparent 60%),
        linear-gradient(180deg, var(--bg0), var(--bg1));
    }
    .wrap{ max-width:980px; margin:0 auto; }
    .top{ display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
    .brand{ display:flex; gap:12px; align-items:center; }
    .logo{
      width:44px; height:44px; border-radius:14px;
      background: linear-gradient(135deg, rgba(124,92,255,.9), rgba(34,197,94,.7));
      box-shadow: var(--shadow);
      border:1px solid rgba(255,255,255,.14);
      position:relative; overflow:hidden;
    }
    .logo:after{
      content:""; position:absolute; inset:-40%;
      background: radial-gradient(circle, rgba(255,255,255,.35), transparent 60%);
      transform: rotate(20deg);
    }
    h1{ font-size:18px; margin:0; letter-spacing:.2px; }
    .sub{ font-size:12px; color:var(--muted); margin-top:2px; }
    .pill{
      font-size:12px; color:var(--muted);
      padding:8px 12px; border:1px solid var(--stroke); border-radius:999px;
      background: rgba(255,255,255,.05); backdrop-filter: blur(10px);
    }
    .grid{ display:grid; grid-template-columns: 1.05fr .95fr; gap:14px; }
    @media (max-width: 860px){ .grid{ grid-template-columns: 1fr; } }
    .card{
      background: linear-gradient(180deg, var(--card), var(--card2));
      border:1px solid var(--stroke);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding:14px;
      backdrop-filter: blur(10px);
    }
    .card h2{
      font-size:14px; margin:0 0 10px 0;
      color: rgba(234,240,255,.92);
      display:flex; align-items:center; justify-content:space-between;
    }
    .hint{ font-size:12px; color:var(--muted); }
    .statRow{ display:grid; grid-template-columns: 1fr 1fr; gap:10px; }
    .stat{
      border:1px solid rgba(255,255,255,.10);
      border-radius: 14px;
      padding:12px;
      background: rgba(0,0,0,.16);
      position:relative;
      overflow:hidden;
    }
    .stat:before{
      content:""; position:absolute; inset:0;
      background: radial-gradient(220px 120px at 10% 10%, rgba(124,92,255,.22), transparent 60%),
                  radial-gradient(220px 120px at 90% 90%, rgba(34,197,94,.16), transparent 60%);
      pointer-events:none;
    }
    .label{ font-size:12px; color:var(--muted); }
    .value{ font-size:26px; font-weight:800; margin-top:6px; letter-spacing:.2px; }
    .unit{ font-size:12px; color:var(--muted); margin-left:6px; font-weight:600; }
    .mini{ margin-top:8px; font-size:12px; color:var(--muted); display:flex; justify-content:space-between; }
    .dot{
      display:inline-block; width:8px; height:8px; border-radius:999px;
      margin-right:8px; vertical-align:middle;
      background: var(--warn);
      box-shadow: 0 0 16px rgba(245,158,11,.55);
    }
    .dot.ok{ background: var(--accent2); box-shadow: 0 0 16px rgba(34,197,94,.55); }
    .dot.bad{ background: var(--danger); box-shadow: 0 0 16px rgba(239,68,68,.55); }
    .btnRow{ display:flex; flex-wrap:wrap; gap:10px; }
    button{
      border:1px solid rgba(255,255,255,.12);
      background: rgba(255,255,255,.06);
      color: var(--text);
      padding:10px 12px;
      border-radius: 14px;
      cursor:pointer;
      font-weight:700;
    }
    button.primary{ background: rgba(124,92,255,.18); border-color: rgba(124,92,255,.35); }
    button.good{ background: rgba(34,197,94,.16); border-color: rgba(34,197,94,.35); }
    button.danger{ background: rgba(239,68,68,.14); border-color: rgba(239,68,68,.32); }
    .field{ display:flex; gap:10px; margin-top:10px; flex-wrap:wrap; }
    input, select{
      flex:1; min-width: 160px;
      border:1px solid rgba(255,255,255,.12);
      background: rgba(0,0,0,.18);
      color: var(--text);
      padding:10px 12px;
      border-radius: 14px;
      outline:none;
    }
    .toast{
      margin-top:10px;
      padding:10px 12px;
      border-radius: 14px;
      border:1px solid rgba(255,255,255,.10);
      background: rgba(0,0,0,.18);
      color: var(--muted);
      min-height: 40px;
    }
    .toast strong{ color: rgba(234,240,255,.9); }
    .foot{ margin-top:14px; font-size:12px; color: var(--muted); }
    code{ color: rgba(234,240,255,.9); }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <div class="brand">
        <div class="logo"></div>
        <div>
          <h1>ESP32 IoT Panel</h1>
          <div class="sub">Dashboard + Control (single page, no full-page auto refresh)</div>
        </div>
      </div>
      <div class="pill">Live update: <span id="poll">2s</span> • API: <code>/api</code></div>
    </div>

    <div class="grid">
      <div class="card">
        <h2>
          Sensors Dashboard
          <span class="hint"><span id="statusDot" class="dot"></span><span id="statusTxt">waiting...</span></span>
        </h2>

        <div class="statRow">
          <div class="stat">
            <div class="label">Temperature (DHT11)</div>
            <div class="value"><span id="tempVal">--</span><span class="unit">°C</span></div>
            <div class="mini"><span>Updated</span><span id="tstamp">--:--:--</span></div>
          </div>
          <div class="stat">
            <div class="label">Distance (HC-SR04)</div>
            <div class="value"><span id="distVal">--</span><span class="unit">cm</span></div>
            <div class="mini"><span>Updated</span><span id="dstamp">--:--:--</span></div>
          </div>
        </div>

        <div class="foot">Tip: Values update with <code>fetch()</code> (no reload).</div>
      </div>

      <div class="card">
        <h2>Control Center <span class="hint">LED + LCD</span></h2>

        <div class="btnRow">
          <button class="good" onclick="act('/on','LED ON ✅')">LED ON</button>
          <button class="danger" onclick="act('/off','LED OFF ✅')">LED OFF</button>
          <button class="primary" onclick="act('/lcd/distance','Distance → LCD line 1 ✅')">LCD: Distance</button>
          <button class="primary" onclick="act('/lcd/temp','Temp → LCD line 2 ✅')">LCD: Temp</button>
          <button onclick="act('/lcd/clear','LCD cleared ✅')">Clear LCD</button>
        </div>

        <div class="field">
          <select id="line">
            <option value="0">LCD Line 1</option>
            <option value="1">LCD Line 2</option>
          </select>
          <input id="msg" placeholder="Type message for LCD (repeat scroll if > 16 chars)" />
          <button class="primary" onclick="sendMsg()">Send</button>
        </div>

        <div class="toast" id="toast"><strong>Status:</strong> Ready.</div>
        <div class="foot">LCD scroll repeats (ESP32 will be busy during scroll; limited to a few seconds).</div>
      </div>
    </div>
  </div>

<script>
  const toast = (t) => { document.getElementById('toast').innerHTML = '<strong>Status:</strong> ' + t; };

  async function act(path, okText){
    try{
      await fetch(path, {cache:'no-store'});
      toast(okText);
    }catch(e){
      toast('Action failed ❌');
    }
  }

  async function sendMsg(){
    const v = document.getElementById('msg').value || '';
    const line = document.getElementById('line').value || '0';
    const qs = encodeURIComponent(v);
    await act('/lcd/text?line=' + line + '&msg=' + qs, 'Message sent to LCD ✅');
  }

  async function poll(){
    try{
      const r = await fetch('/api', {cache:'no-store'});
      const j = await r.json();

      document.getElementById('tempVal').textContent = (j.temp === null) ? 'Err' : j.temp;
      document.getElementById('distVal').textContent = (j.dist === null) ? 'Err' : j.dist;

      const now = new Date();
      const hh = String(now.getHours()).padStart(2,'0');
      const mm = String(now.getMinutes()).padStart(2,'0');
      const ss = String(now.getSeconds()).padStart(2,'0');
      document.getElementById('tstamp').textContent = hh+':'+mm+':'+ss;
      document.getElementById('dstamp').textContent = hh+':'+mm+':'+ss;

      const dot = document.getElementById('statusDot');
      const st  = document.getElementById('statusTxt');

      if (j.temp === null || j.dist === null){
        dot.className = 'dot bad';
        st.textContent = 'sensor error';
      }else{
        dot.className = 'dot ok';
        st.textContent = 'live';
      }
    }catch(e){
      const dot = document.getElementById('statusDot');
      const st  = document.getElementById('statusTxt');
      dot.className = 'dot bad';
      st.textContent = 'api offline';
    }
  }

  poll();
  setInterval(poll, 2000);
</script>

</body>
</html>
"""

def json_api(temp, dist):
    t = "null" if temp is None else str(temp)
    d = "null" if dist is None else str(dist)
    body = '{"temp":%s,"dist":%s}' % (t, d)
    return "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nCache-Control: no-store\r\n\r\n" + body

# ================= WEB SERVER =================
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(5)
print("Listening on", addr)

while True:
    cl, remote = s.accept()
    try:
        req = cl.recv(1024).decode()
        first = req.split("\r\n")[0]
        parts = first.split(" ")
        path = parts[1] if len(parts) > 1 else "/"

        # ---------- API ----------
        if path.startswith("/api"):
            temp = read_temp_c()
            dist = read_distance_cm()
            cl.send(json_api(temp, dist))

        # ---------- LED ----------
        elif path == "/on":
            led.value(1)
            cl.send("HTTP/1.1 204 No Content\r\n\r\n")

        elif path == "/off":
            led.value(0)
            cl.send("HTTP/1.1 204 No Content\r\n\r\n")

        # ---------- LCD ----------
        elif path.startswith("/lcd/distance"):
            d = read_distance_cm()
            msg = "Distance: Err" if d is None else ("Distance:%scm" % d)
            lcd_write(0, msg)
            cl.send("HTTP/1.1 204 No Content\r\n\r\n")

        elif path.startswith("/lcd/temp"):
            t = read_temp_c()
            msg = "Temp: Err" if t is None else ("Temp:%sC" % t)
            lcd_write(1, msg)
            cl.send("HTTP/1.1 204 No Content\r\n\r\n")

        elif path.startswith("/lcd/clear"):
            lcd.clear()
            cl.send("HTTP/1.1 204 No Content\r\n\r\n")

        elif path.startswith("/lcd/text"):
            raw = get_query_value(path, "msg")
            line = get_query_value(path, "line")
            line = int(line) if line.isdigit() else 0

            text = url_decode(raw).strip()
            if text == "":
                text = "Hello LCD"

            # ✅ repeat scroll if >16, and stop after 8 seconds (adjust!)
            lcd_scroll_repeat(line, text, delay=0.22, repeat=True, max_seconds=8)

            cl.send("HTTP/1.1 204 No Content\r\n\r\n")

        # ---------- UI ----------
        else:
            cl.send(html_page())

    except:
        try:
            cl.send("HTTP/1.1 500 OK\r\nContent-Type:text/plain\r\n\r\nError")
        except:
            pass
    finally:
        cl.close()
