# LAB2 – IoT Webserver with LED, Sensors, and LCD Control

## 1. Overview
This project implements an **ESP32-based IoT webserver** using **MicroPython**. The system allows users to:

- Control an LED from a web browser
- Read temperature (DHT11) and distance (HC-SR04 ultrasonic sensor)
- Display sensor data on a **16×2 I2C LCD** using web buttons
- Send **custom text from a web textbox** to the LCD

The lab demonstrates **event-driven IoT design**, integrating a web interface with physical hardware components.

---

## 2. Learning Outcomes
By completing this lab, the student is able to:

- Implement a MicroPython-based webserver on ESP32
- Control GPIO devices via HTTP requests
- Read and display sensor data on a web UI
- Interface and control an I2C LCD using web commands
- Document hardware wiring and system behavior

---

## 3. Hardware & Software Requirements

### Hardware
- ESP32 Dev Board (MicroPython flashed)
- LED + resistor
- DHT11 Temperature Sensor
- HC-SR04 Ultrasonic Distance Sensor
- 16×2 LCD with I2C backpack
- Breadboard and jumper wires
- USB cable

### Software
- MicroPython firmware (ESP32)
- Thonny IDE
- Web browser (Chrome / Firefox)
- Wi-Fi network

---

## 4. Wiring Connections

### LED
| ESP32 Pin | LED |
|---------|-----|
| GPIO2 | Anode (+) |
| GND | Cathode (-) |

### DHT11 Sensor
| ESP32 Pin | DHT11 |
|---------|-------|
| 5V | VCC |
| GPIO4 | DATA |
| GND | GND |

### Ultrasonic Sensor (HC-SR04)
| ESP32 Pin | HC-SR04 |
|---------|----------|
| 5V | VCC |
| GPIO27 | TRIG |
| GPIO26 | ECHO |
| GND | GND |

### LCD 16×2 (I2C)
| ESP32 Pin | LCD |
|---------|-----|
| 5V | VCC |
| GND | GND |
| GPIO21 | SDA |
| GPIO22 | SCL |

> 📷 **Note:** Include a wiring photo or diagram here.

---

## 5. Setup Instructions

1. Flash **MicroPython firmware** onto ESP32
2. Open **Thonny IDE**
3. Upload the following files to ESP32:
   - `main.py`
   - `lcd_api.py`
   - `i2c_lcd.py`
4. Edit Wi-Fi credentials inside `main.py`:
   ```python
   SSID = "YOUR_WIFI_NAME"
   PASSWORD = "YOUR_WIFI_PASSWORD"
   ```
5. Run `main.py`
6. Note the **ESP32 IP address** printed in the console
7. Open a browser and access:
   ```
   http://ESP32_IP_ADDRESS
   ```

---

## 6. Web Interface Usage

### LED Control
- Click **ON** → LED turns ON
- Click **OFF** → LED turns OFF

### Sensor Monitoring
- Temperature (°C) and Distance (cm) are displayed on the web page
- Values refresh automatically every 1–2 seconds

### LCD Control
- **Show Temp** → Displays temperature on LCD
- **Show Distance** → Displays distance on LCD

### Custom Text to LCD
- Enter text in the textbox
- Click **Send**
- The message appears on the LCD

---

## 7. Evidence Checklist

✔ Video showing LED ON/OFF from browser  
✔ Screenshot of web page displaying sensor values  
✔ Photo of LCD showing temperature and distance  
✔ Video showing custom text sent from browser to LCD  

---

## 8. Project Structure
```
LAB2_IoT_Webserver/
│── main.py
│── lcd_api.py
│── i2c_lcd.py
│── README.md
│── screenshots/
│── demo_video.mp4
```

---

## 9. Demo Video Content (60–90 seconds)

The demo video demonstrates:
1. LED ON/OFF control from browser
2. Real-time sensor values on web page
3. Temperature and distance displayed on LCD via buttons
4. Custom text typed in browser appearing on LCD

---

## 10. Academic Integrity

This project is completed individually and follows the academic integrity guidelines. All code and documentation are original and properly implemented for educational purposes.

---

## 11. Author

**Student Name:** ____________________  
**Course:** IoT / Embedded Systems  
**Lab:** LAB2 – IoT Webserver with LCD Control
