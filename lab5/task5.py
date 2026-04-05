from machine import I2C, Pin, PWM
import network
import socket
import time
from neopixel import NeoPixel
from tcs34725 import TCS34725

# --- WiFi credentials ---
SSID = "Robotic WIFI"        
PASSWORD = "rbtWIFI@2025" 

# --- Hardware setup ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TCS34725(i2c)
np = NeoPixel(Pin(23), 24)
ena = PWM(Pin(14), freq=1000)
in1 = Pin(26, Pin.OUT)
in2 = Pin(27, Pin.OUT)

# --- Connect to WiFi ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
print("Connecting to WiFi...")
while not wlan.isconnected():
    time.sleep(0.5)
print("Connected! IP:", wlan.ifconfig()[0])

# --- Start HTTP server ---
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', 80))
server.listen(5)
server.setblocking(False)
print("Server started on port 80")

# --- Global state ---
current_color = "UNKNOWN"

# --- Color classification ---
def classify_color(r, g, b):
    if r < 50 and g < 50 and b < 50:
        return "UNKNOWN"
    if r > g * 1.3 and r > b * 1.3:
        return "RED"
    elif g > r * 1.3 and g > b * 1.3:
        return "GREEN"
    elif b > r * 1.3 and b > g * 1.3:
        return "BLUE"
    else:
        return "UNKNOWN"

# --- NeoPixel control ---
def set_neopixel(color):
    if color == "RED":
        rgb = (255, 0, 0)
    elif color == "GREEN":
        rgb = (0, 255, 0)
    elif color == "BLUE":
        rgb = (0, 0, 255)
    else:
        rgb = (0, 0, 0)
    for i in range(np.n):
        np[i] = rgb
    np.write()

# --- NeoPixel manual RGB ---
def set_neopixel_rgb(r, g, b):
    for i in range(np.n):
        np[i] = (r, g, b)
    np.write()

# --- Motor control ---
def set_motor(color):
    if color == "UNKNOWN":
        ena.duty(0)
        in1.value(0)
        in2.value(0)
    else:
        in1.value(1)
        in2.value(0)
        if color == "RED":
            ena.duty(900)
        elif color == "GREEN":
            ena.duty(700)
        elif color == "BLUE":
            ena.duty(500)

# --- Handle HTTP requests ---
def handle_request(request):
    global current_color

    # GET /color → return detected color
    if "/color" in request:
        return current_color

    # GET /forward
    elif "/forward" in request:
        in1.value(1)
        in2.value(0)
        ena.duty(700)
        return "OK"

    # GET /backward
    elif "/backward" in request:
        in1.value(0)
        in2.value(1)
        ena.duty(700)
        return "OK"

    # GET /stop
    elif "/stop" in request:
        in1.value(0)
        in2.value(0)
        ena.duty(0)
        return "OK"

    # GET /rgb?r=255&g=0&b=0
    elif "/rgb" in request:
        try:
            r = int(request.split("r=")[1].split("&")[0])
            g = int(request.split("g=")[1].split("&")[0])
            b = int(request.split("b=")[1].split(" ")[0])
            set_neopixel_rgb(r, g, b)
            return "OK"
        except:
            return "ERROR"

    return "OK"

# --- Main loop ---
while True:
    # Read sensor
    r, g, b, c = sensor.read_raw()
    current_color = classify_color(r, g, b)
    set_neopixel(current_color)
    set_motor(current_color)
    print(f"R={r} G={g} B={b} → {current_color}")

    # Check for app request
    try:
        conn, addr = server.accept()
        request = conn.recv(512).decode()
        response = handle_request(request)
        conn.send("HTTP/1.1 200 OK\r\nAccess-Control-Allow-Origin: *\r\n\r\n" + response)
        conn.close()
    except:
        pass

    time.sleep(0.3)