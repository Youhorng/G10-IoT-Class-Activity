from machine import Pin, SPI
from mfrc522 import MFRC522
import network
import urequests
import time
import ntptime
import sdcard, os

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
SSID       = "Robotic WIFI"
PASSWORD   = "rbtWIFI@2025"
PROJECT_ID = "rfid-attendance-8bdd2"

FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/{}/databases/(default)/documents/attendance".format(PROJECT_ID)

# ─────────────────────────────────────────────
# STUDENT DATABASE
# ─────────────────────────────────────────────
STUDENTS = {
    "221182382556": {"name": "Hoeun Visai",  "student_id": "2023016", "major": "Cybersecurity"},
    "654514650204": {"name": "Kean Youhong",  "student_id": "2023221", "major": "Infomation and Communication Technology"},
    "152618618918": {"name": "Panhawath Ek",  "student_id": "2025028", "major": "Data Analysis"},
    "2411442021736": {"name": "Chhoeun Sovorthanak",  "student_id": "2023009", "major": "Infomation and Communication Technology"},
}

# ─────────────────────────────────────────────
# HARDWARE INIT
# ─────────────────────────────────────────────

# 🔊 Buzzer
buzzer = Pin(4, Pin.OUT)
buzzer.value(0)

# 📡 RFID → SPI1
spi_rfid = SPI(1, baudrate=1000000,
               sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = MFRC522(spi=spi_rfid, gpioRst=Pin(22), gpioCs=Pin(16))

# 💾 SD Card → SPI2 (FIXED)
sd_spi = SPI(2, baudrate=1000000,
             sck=Pin(14), mosi=Pin(15), miso=Pin(2))

sd = sdcard.SDCard(sd_spi, Pin(13))  # CS = 13
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

print("SD card mounted")

# ─────────────────────────────────────────────
# WIFI CONNECT
# ─────────────────────────────────────────────
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

print("Connecting WiFi", end="")
while not wifi.isconnected():
    print(".", end="")
    time.sleep(0.5)

print("\nConnected:", wifi.ifconfig())

# ─────────────────────────────────────────────
# TIME SYNC
# ─────────────────────────────────────────────
try:
    ntptime.settime()
    print("Time synced")
except Exception as e:
    print("NTP failed:", e)

# ─────────────────────────────────────────────
# FUNCTIONS
# ─────────────────────────────────────────────

def get_datetime():
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5])

def beep(ms):
    buzzer.value(1)
    time.sleep_ms(ms)
    buzzer.value(0)

def ensure_csv():
    try:
        open("/sd/attendance.csv", "r").close()
    except:
        with open("/sd/attendance.csv", "w") as f:
            f.write("UID,Name,StudentID,Major,DateTime\n")
        print("CSV file created")

def save_to_sd(uid, student, dt):
    row = "{},{},{},{},{}\n".format(
        uid,
        student["name"],
        student["student_id"],
        student["major"],
        dt
    )
    try:
        with open("/sd/attendance.csv", "a") as f:
            f.write(row)
        print("Saved:", row.strip())
        print(os.listdir("/sd"))
    except Exception as e:
        print("SD error:", e)

def send_to_firestore(uid, student, dt):
    data = {
        "fields": {
            "uid": {"stringValue": uid},
            "name": {"stringValue": student["name"]},
            "student_id": {"stringValue": student["student_id"]},
            "major": {"stringValue": student["major"]},
            "datetime": {"stringValue": dt}
        }
    }

    try:
        res = urequests.post(FIRESTORE_URL, json=data)
        print("Firestore OK")
        res.close()
    except Exception as e:
        print("Firestore error:", e)

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────
ensure_csv()
print("\nScan RFID card...")

while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)

    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()

        if stat == rdr.OK:
            uid_str = "".join([str(x) for x in uid])
            dt = get_datetime()

            print("\nUID:", uid_str)
            student = STUDENTS.get(uid_str)

            if student:
                print("VALID:", student["name"])
                beep(300)

                save_to_sd(uid_str, student, dt)
                send_to_firestore(uid_str, student, dt)

            else:
                print("UNKNOWN CARD")
                beep(3000)

            time.sleep(2)