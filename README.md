# ICT 360-001: Introduction to Internet of Things

**Course:** ICT 360-001 - Introduction to Internet of Things  
**Term:** Spring 2026  

---

## Overview

This repository contains all laboratory activities, projects, and assignments for **ICT 360-001: Introduction to Internet of Things**. Each lab focuses on hands-on implementation of IoT concepts using ESP32 microcontrollers, sensors, actuators, and cloud platforms.

## Course Objectives

- Design and implement ESP32-based IoT systems using MicroPython
- Integrate multiple sensors and actuators into cohesive systems
- Develop web-based and cloud-based control interfaces
- Implement event-driven programming and real-time data processing
- Document technical projects with professional standards

## Repository Structure

```
iot-class/
├── lab1-temperature-sensor-with-relay-control-telegram/
│   └── Temperature monitoring with Telegram bot integration
│
├── lab2-webserver-lcd-control/
│   └── ESP32 webserver with LED, sensors, and LCD display
│
├── lab3-iot-blynk-ir-servo/
│   └── Smart gate control with Blynk, IR sensor, and servo motor
│
└── README.md (this file)
```

## Laboratory Activities

### [Lab 1: Temperature Sensor with Relay Control & Telegram](./lab1-temperature-sensor-with-relay-control-telegram)

**Topics:** Sensor integration, relay control, Telegram bot API  
**Hardware:** ESP32, DHT11/DHT22, relay module  
**Skills:** Temperature monitoring, remote notifications, automated control

### [Lab 2: IoT Webserver with LED, Sensors, and LCD Control](./lab2-webserver-lcd-control)

**Topics:** Web server development, sensor reading, LCD display  
**Hardware:** ESP32, DHT11, HC-SR04, LCD 16×2 with I²C  
**Skills:** HTTP endpoints, JSON APIs, real-time web interfaces, hardware control

### [Lab 3: IoT Smart Gate Control with Blynk, IR Sensor, Servo Motor, and TM1637](./lab3-iot-blynk-ir-servo)

**Topics:** Cloud IoT platforms, object detection, servo actuation, 7-segment displays  
**Hardware:** ESP32, IR sensor, servo motor, TM1637 display  
**Skills:** Blynk integration, automatic/manual control modes, event counting, mobile app dashboards

## Technologies & Tools

- **Microcontroller:** ESP32 Dev Board
- **Programming Language:** MicroPython
- **IDE:** Thonny Python IDE
- **Cloud Platforms:** Blynk IoT
- **Communication:** Wi-Fi, HTTP, Telegram Bot API
- **Version Control:** Git & GitHub

## Common Equipment

- ESP32 Dev Board (MicroPython firmware)
- Breadboard and jumper wires
- USB cable for programming
- Various sensors (DHT11, HC-SR04, IR sensor)
- Actuators (LED, relay, servo motor)
- Displays (LCD 16×2 I²C, TM1637 7-segment)
- Smartphone (for Blynk app)

## Getting Started

### Prerequisites

1. **Install Thonny IDE**
   - Download from [thonny.org](https://thonny.org)
   - Configure for MicroPython on ESP32

2. **Flash MicroPython Firmware**
   - Download ESP32 firmware from [micropython.org](https://micropython.org/download/esp32/)
   - Flash using esptool or Thonny

3. **Setup Wi-Fi Access**
   - Ensure 2.4GHz Wi-Fi network availability
   - Note SSID and password for configuration

### Running a Lab

1. Navigate to the specific lab directory
2. Read the lab's `README.md` for detailed instructions
3. Wire components according to the wiring diagram
4. Update configuration (Wi-Fi credentials, API tokens)
5. Upload required files to ESP32 using Thonny
6. Run `main.py` and monitor serial output

## Documentation Standards

Each lab includes:

- **README.md** - Complete setup and usage instructions
- **Wiring diagrams** - Visual component connections
- **Code comments** - Inline documentation
- **Screenshots/Videos** - Evidence of working implementation
- **Troubleshooting guide** - Common issues and solutions

