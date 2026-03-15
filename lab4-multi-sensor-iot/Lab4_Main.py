import network
import time
import machine
import urequests

# ==========================================
# CONFIG
# ==========================================
WIFI_SSID = "Robotic WIFI"
WIFI_PASS = "rbtWIFI@2025"

NODE_RED_URL = "http://10.30.0.207:1880/iot/gas"

MQ5_PIN = 33
I2C_SCL = 22
I2C_SDA = 21

SEND_INTERVAL = 3
WINDOW_SIZE = 5

# ==========================================
# WIFI CONNECT
# ==========================================
def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)

    if not wifi.isconnected():
        print("Connecting to WiFi...")
        wifi.connect(WIFI_SSID, WIFI_PASS)

        timeout = 15
        start = time.time()
        while not wifi.isconnected():
            if time.time() - start > timeout:
                print("WiFi connection timeout")
                return None
            time.sleep(1)

    print("WiFi connected:", wifi.ifconfig())
    return wifi

# ==========================================
# MQ-5 ADC SETUP
# ==========================================
mq5 = machine.ADC(machine.Pin(MQ5_PIN))
mq5.atten(machine.ADC.ATTN_11DB)
mq5.width(machine.ADC.WIDTH_12BIT)

# ==========================================
# I2C SETUP
# ==========================================
i2c = machine.I2C(0, scl=machine.Pin(I2C_SCL), sda=machine.Pin(I2C_SDA), freq=100000)

# ==========================================
# HELPER
# ==========================================
def bcd_to_dec(val):
    return ((val >> 4) * 10) + (val & 0x0F)

# ==========================================
# DS3231 RTC
# ==========================================
class DS3231:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr

    def get_datetime(self):
        data = self.i2c.readfrom_mem(self.addr, 0x00, 7)
        second = bcd_to_dec(data[0] & 0x7F)
        minute = bcd_to_dec(data[1])
        hour   = bcd_to_dec(data[2] & 0x3F)
        day    = bcd_to_dec(data[4])
        month  = bcd_to_dec(data[5] & 0x1F)
        year   = 2000 + bcd_to_dec(data[6])

        return year, month, day, hour, minute, second

    def get_timestamp(self):
        y, mo, d, h, mi, s = self.get_datetime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(y, mo, d, h, mi, s)

# ==========================================
# MLX90614
# ==========================================
class MLX90614:
    def __init__(self, i2c, addr=0x5A):
        self.i2c = i2c
        self.addr = addr

    def read_temp(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 3)
        raw = data[0] | (data[1] << 8)
        temp = (raw * 0.02) - 273.15
        return temp

    def ambient_temp(self):
        return self.read_temp(0x06)

    def object_temp(self):
        return self.read_temp(0x07)

# ==========================================
# BMP280
# ==========================================
class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr

        self.i2c.writeto_mem(self.addr, 0xF4, b'\x27')
        self.i2c.writeto_mem(self.addr, 0xF5, b'\xA0')

        self.dig_T1 = self.readU16LE(0x88)
        self.dig_T2 = self.readS16LE(0x8A)
        self.dig_T3 = self.readS16LE(0x8C)

        self.dig_P1 = self.readU16LE(0x8E)
        self.dig_P2 = self.readS16LE(0x90)
        self.dig_P3 = self.readS16LE(0x92)
        self.dig_P4 = self.readS16LE(0x94)
        self.dig_P5 = self.readS16LE(0x96)
        self.dig_P6 = self.readS16LE(0x98)
        self.dig_P7 = self.readS16LE(0x9A)
        self.dig_P8 = self.readS16LE(0x9C)
        self.dig_P9 = self.readS16LE(0x9E)

        self.t_fine = 0

    def readU16LE(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return data[0] | (data[1] << 8)

    def readS16LE(self, reg):
        result = self.readU16LE(reg)
        if result > 32767:
            result -= 65536
        return result

    def read_raw_temp(self):
        data = self.i2c.readfrom_mem(self.addr, 0xFA, 3)
        return ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4

    def read_raw_pressure(self):
        data = self.i2c.readfrom_mem(self.addr, 0xF7, 3)
        return ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4

    def temperature(self):
        adc_T = self.read_raw_temp()
        var1 = (((adc_T >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc_T >> 4) - self.dig_T1) * ((adc_T >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        T = (self.t_fine * 5 + 128) >> 8
        return T / 100.0

    def pressure(self):
        self.temperature()
        adc_P = self.read_raw_pressure()

        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33

        if var1 == 0:
            return 0

        p = 1048576 - adc_P
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)

        return p / 25600.0

    def altitude(self, sea_level_hpa=1013.25):
        pressure = self.pressure()
        return 44330 * (1.0 - (pressure / sea_level_hpa) ** 0.1903)

# ==========================================
# SENSOR INIT
# ==========================================
rtc = DS3231(i2c)
mlx = MLX90614(i2c)
bmp = BMP280(i2c, addr=0x76)   # change to 0x77 if needed

# ==========================================
# TASK 1 - MOVING AVERAGE
# ==========================================
gas_readings = []

def get_moving_average(new_value):
    gas_readings.append(new_value)
    if len(gas_readings) > WINDOW_SIZE:
        gas_readings.pop(0)
    return sum(gas_readings) / len(gas_readings)

# ==========================================
# TASK 2 - RISK CLASSIFICATION
# ==========================================
def classify_risk(avg_value):
    if avg_value < 2100:
        return "SAFE"
    elif avg_value < 2600:
        return "WARNING"
    else:
        return "DANGER"

# ==========================================
# TASK 3 - FEVER DETECTION
# ==========================================
def get_fever_flag(body_temp):
    return 1 if body_temp >= 32.5 else 0

# ==========================================
# SEND TO NODE-RED
# ==========================================
def send_to_nodered(payload):
    try:
        response = urequests.post(NODE_RED_URL, json=payload)
        print("Sent to Node-RED:", response.status_code)
        print("Response:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data:", e)

# ==========================================
# MAIN
# ==========================================
def main():
    connect_wifi()
    print("Task 4: Full Multi-Sensor Monitoring Started")
    print("Using URL:", NODE_RED_URL)

    while True:
        try:
            # MQ-5
            raw_value = mq5.read()
            avg_value = get_moving_average(raw_value)
            risk_level = classify_risk(avg_value)

            # MLX90614
            body_temp = mlx.object_temp()
            fever_flag = get_fever_flag(body_temp)

            # BMP280
            room_temp = bmp.temperature()
            pressure = bmp.pressure()
            altitude = bmp.altitude()

            # DS3231
            timestamp = rtc.get_timestamp()

            payload = {
                "timestamp": timestamp,
                "gas_raw": raw_value,
                "gas_avg": round(avg_value, 2),
                "risk_level": risk_level,
                "body_temp": round(body_temp, 2),
                "fever_flag": fever_flag,
                "room_temp": round(room_temp, 2),
                "pressure": round(pressure, 2),
                "altitude": round(altitude, 2)
            }

            print("----------------------------")
            print("Timestamp       :", timestamp)
            print("Raw MQ-5 Value  :", raw_value)
            print("Average MQ-5    :", round(avg_value, 2))
            print("Stored Readings :", gas_readings)
            print("Risk Level      :", risk_level)
            print("Body Temp       :", round(body_temp, 2), "C")
            print("Fever Flag      :", fever_flag)
            print("Room Temp       :", round(room_temp, 2), "C")
            print("Pressure        :", round(pressure, 2), "hPa")
            print("Altitude        :", round(altitude, 2), "m")

            send_to_nodered(payload)

        except Exception as e:
            print("Loop error:", e)

        time.sleep(SEND_INTERVAL)

# Run
main()