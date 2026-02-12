# Lab 3 - IoT Smart Gate Control with Blynk, IR Sensor, Servo Motor, and TM1637

## Overview

In this lab, we will design and implement an ESP32-based IoT system using MicroPython and the Blynk platform. The system integrates an IR sensor for object detection, a servo motor for physical actuation, and a TM1637 7-segment display for real-time local feedback. We will use the Blynk mobile application to remotely control the system, monitor sensor status, and observe system behavior.

## Learning Outcomes (CLO Alignment)

- Integrate multiple sensors and actuators into a single IoT system using ESP32
- Use Blynk to remotely control hardware and visualize system status
- Implement automatic and manual control logic based on sensor input and cloud commands
- Display system status and numerical data using a TM1637 7-segment display
- Document system wiring, logic flow, and IoT behavior clearly

## Hardware

- ESP32 Dev Board (MicroPython firmware flashed)
- IR Sensor Module (digital output)
- Servo Motor (SG90 or similar)
- TM1637 4-Digit 7-Segment Display
- Breadboard, jumper wires
- USB cable + laptop with Thonny
- Smartphone with Blynk app installed

## Equipment

- ESP32 dev board
- IR sensor module
- Servo motor (SG90)
- TM1637 7-segment display
- Breadboard, jumper wires
- USB cable + laptop with Thonny
- Wi-Fi access
- Smartphone (iOS/Android) with Blynk app

## Wiring

This is the diagram for wiring setup with the available equipment.

![Wiring Diagram](./screenshot/wiring_setup.png)

![Component Setup](./screenshot/component_setup.jpg)

### Pin Connections

| Component     | ESP32 Pin | Description                        |
| ------------- | --------- | ---------------------------------- |
| IR Sensor VCC | 3.3V      | Power supply for IR sensor         |
| IR Sensor GND | GND       | Ground                             |
| IR Sensor OUT | GPIO13    | Digital output (LOW when detected) |
| Servo VCC     | 5V        | Power supply for servo motor       |
| Servo GND     | GND       | Ground                             |
| Servo Signal  | GPIO14    | PWM control signal                 |
| TM1637 VCC    | 3.3V      | Power supply for display           |
| TM1637 GND    | GND       | Ground                             |
| TM1637 CLK    | GPIO18    | Clock signal                       |
| TM1637 DIO    | GPIO19    | Data I/O signal                    |

## Configuration

These are the main configuration settings to run all the tasks in this activity.

- Blynk authentication token
- Wi-Fi SSID and password
- GPIO pin assignments
- Servo angle limits

```python
# Blynk Configuration
BLYNK_AUTH = "YOUR_BLYNK_AUTH_TOKEN"

# Wi-Fi Configuration
WIFI_SSID = "YOUR_SSID"
WIFI_PASS = "YOUR_PASSWORD"

# Pin Configuration
IR_SENSOR_PIN = 13
SERVO_PIN = 14
TM1637_CLK = 18
TM1637_DIO = 19

# Servo Configuration
SERVO_CLOSED = 0    # Closed position (degrees)
SERVO_OPEN = 90     # Open position (degrees)
SERVO_DELAY = 2000  # Time to keep gate open (ms)
```

## Setup Instructions

### 1. Blynk Setup

1. Download and install the Blynk app from App Store (iOS) or Google Play (Android)
2. Create a new Blynk account or log in
3. Create a new project:
   - Project name: "Smart Gate Control"
   - Device: ESP32
   - Connection type: Wi-Fi
4. Copy the **Auth Token** sent to your email
5. Add the following widgets to your dashboard:
   - **LED Widget** (Virtual Pin V0) - IR Sensor Status
   - **Slider Widget** (Virtual Pin V1) - Manual Servo Control (0-180)
   - **Value Display** (Virtual Pin V2) - Detection Counter
   - **Switch Widget** (Virtual Pin V3) - Manual Override Mode

### 2. ESP32 Setup

1. Flash MicroPython firmware to ESP32 (if not already done)
2. Wire all components according to the wiring diagram above
3. Download the required library files:
   - `BlynkLib.py` - Blynk library for MicroPython [GitHub](https://github.com/vshymanskyy/blynk-library-python)
   - `tm1637.py` - TM1637 display driver [GitHub](https://github.com/mcauser/micropython-tm1637)
4. Update the configuration in `main.py` with your credentials:
   ```python
   BLYNK_AUTH = "YourAuthTokenFromEmail"
   WIFI_SSID = "YOUR_WIFI_SSID"
   WIFI_PASS = "YOUR_WIFI_PASSWORD"
   ```
5. Upload all files to ESP32 using Thonny:
   - `main.py`
   - `BlynkLib.py`
   - `tm1637.py`
6. Reset the ESP32 or run `main.py`
7. Check the serial monitor for connection status
8. Open the Blynk app and verify the connection

## Usage

### Blynk Dashboard Features

The Blynk mobile app provides remote monitoring and control:

![Blynk Dashboard](./screenshot/blynk_dashboard.png)

#### **Monitoring Widgets**

1. **IR Sensor Status (LED Widget - V0)**
   - Green: Object detected
   - Gray: No object detected
   - Updates in real-time

2. **Detection Counter (Value Display - V2)**
   - Shows total number of detection events
   - Syncs with TM1637 display
   - Resets on ESP32 restart

#### **Control Widgets**

1. **Manual Servo Control (Slider - V1)**
   - Range: 0° to 180°
   - Drag slider to set servo position
   - Works only when manual mode is enabled
   - Real-time servo movement

2. **Manual Override Switch (Switch - V3)**
   - OFF: Automatic mode (IR sensor controls servo)
   - ON: Manual mode (IR sensor ignored, slider controls servo)

### Local Display (TM1637)

The 4-digit 7-segment display shows:

- **Detection counter** - Number of times IR sensor detected an object
- **Leading zeros** - Padded for clarity (e.g., "0042")
- **Brightness** - Adjustable in code (0-7)

### System Behavior

#### Automatic Mode (Default)

1. IR sensor continuously monitors for objects
2. When object detected:
   - Servo rotates to OPEN position (90°)
   - Counter increments by 1
   - TM1637 display updates
   - Blynk counter updates
   - IR status LED turns green
3. After 2 seconds delay:
   - Servo returns to CLOSED position (0°)
4. System ready for next detection

#### Manual Mode

1. User enables manual override switch on Blynk
2. IR sensor readings are ignored
3. User controls servo position via slider (0-180°)
4. Counter does not increment
5. TM1637 shows last counter value

## API / Virtual Pins

The ESP32 communicates with Blynk using virtual pins:

| Virtual Pin | Type   | Direction | Description                          |
| ----------- | ------ | --------- | ------------------------------------ |
| V0          | LED    | ESP → App | IR sensor status (0=clear, 1=detect) |
| V1          | Slider | App → ESP | Manual servo position (0-180)        |
| V2          | Value  | ESP → App | Detection counter                    |
| V3          | Switch | App → ESP | Manual override mode (0=auto, 1=man) |

## Tasks & Checkpoints

### Task 1 - IR Sensor Reading

**Objective:** Read IR sensor digital output using ESP32 and display IR status (Detected / Not Detected) on Blynk.

**Implementation:**

The IR sensor module outputs a digital signal:

- **LOW (0)** when object is detected
- **HIGH (1)** when no object is present

```python
from machine import Pin

ir_sensor = Pin(13, Pin.IN)

def read_ir_sensor():
    return ir_sensor.value() == 0  # Returns True if detected
```

The status is sent to Blynk LED widget on Virtual Pin V0:

```python
# In main loop
ir_detected = read_ir_sensor()
blynk.virtual_write(0, 255 if ir_detected else 0)
```

**Evidence:**

![Task 1 - IR Sensor Status](./screenshot/task1_ir_status.png)

---

### Task 2 - Servo Motor Control via Blynk

**Objective:** Add a Blynk Slider widget to control servo position. Slider position from 0 to 180 degrees and the servo moves following the slider.

**Implementation:**

Servo control is implemented using PWM:

```python
from machine import Pin, PWM
import time

servo = PWM(Pin(14), freq=50)

def set_servo_angle(angle):
    # Convert angle (0-180) to duty cycle (26-128)
    # SG90: 0° = 0.5ms (26), 90° = 1.5ms (77), 180° = 2.5ms (128)
    duty = int(26 + (angle / 180) * 102)
    servo.duty(duty)
    time.sleep_ms(100)
```

Blynk slider handler receives values from Virtual Pin V1:

```python
@blynk.on("V1")
def v1_write_handler(value):
    if manual_mode:  # Only respond in manual mode
        angle = int(value[0])
        set_servo_angle(angle)
```

**Evidence:**

![Task 2 - Servo Control Video](./screenshot/task2_servo_control.gif)

---

### Task 3 - Automatic IR-Servo Action

**Objective:** When IR sensor detects an object, servo opens automatically. After a short delay, servo returns to closed position.

**Implementation:**

The automatic gate logic runs in the main loop:

```python
def auto_gate_control():
    global detection_count

    if not manual_mode:  # Only in automatic mode
        ir_detected = read_ir_sensor()

        if ir_detected and not gate_open:
            # Object detected - open gate
            set_servo_angle(SERVO_OPEN)
            gate_open = True

            # Increment counter
            detection_count += 1
            update_display(detection_count)
            blynk.virtual_write(2, detection_count)

            # Wait before closing
            time.sleep_ms(SERVO_DELAY)

            # Close gate
            set_servo_angle(SERVO_CLOSED)
            gate_open = False
```

**Evidence:**

![Task 3 - Automatic Gate Video](./screenshot/task3_auto_gate.gif)

---

### Task 4 - TM1637 Display Integration

**Objective:** Count the number of IR detection events. Display the counter value on the TM1637 display and send the same value to Blynk numeric display widget.

**Implementation:**

TM1637 display initialization and update:

```python
import tm1637
from machine import Pin

# Initialize TM1637
tm = tm1637.TM1637(clk=Pin(18), dio=Pin(19))
tm.brightness(5)  # Set brightness (0-7)

def update_display(count):
    # Convert count to 4-digit string with leading zeros
    digits = "{:04d}".format(count)

    # Display on TM1637
    tm.show(digits)

    # Send to Blynk
    blynk.virtual_write(2, count)
```

Counter increments on each detection:

```python
detection_count = 0

# In IR detection handler
if ir_detected:
    detection_count += 1
    update_display(detection_count)
```

**Evidence:**

![Task 4 - TM1637 Display](./screenshot/task4_display_sync.gif)

---

### Task 5 - Manual Override Mode

**Objective:** Add a Blynk switch to enable/disable automatic IR mode. When manual mode is active, IR sensor is ignored.

**Implementation:**

Manual override is controlled by a Blynk switch on Virtual Pin V3:

```python
manual_mode = False

@blynk.on("V3")
def v3_write_handler(value):
    global manual_mode
    manual_mode = int(value[0]) == 1

    if manual_mode:
        print("Manual mode enabled")
    else:
        print("Automatic mode enabled")
        # Return servo to closed position
        set_servo_angle(SERVO_CLOSED)
```

The main loop checks the mode before processing IR sensor:

```python
def main_loop():
    if manual_mode:
        # Manual mode - slider controls servo
        # IR sensor is ignored
        pass
    else:
        # Automatic mode - IR sensor controls servo
        auto_gate_control()
```

**Evidence:**

![Task 5 - Manual Override Demo](./screenshot/task5_manual_override.gif)

---

**Demo Video:** [YouTube Link](https://youtube.com/shorts/YOUR_VIDEO_ID)

---

## Technical Features

### 🔧 **Key Implementation Highlights**

1. **Event-Driven Architecture**
   - Blynk virtual pin handlers for real-time cloud communication
   - Non-blocking main loop for responsive behavior
   - Asynchronous sensor reading and actuation

2. **State Management**
   - `manual_mode` flag for mode switching
   - `gate_open` flag to prevent duplicate triggers
   - `detection_count` persistent counter

3. **PWM Servo Control**
   - 50Hz frequency for standard servo motors
   - Duty cycle calculation for precise angle control
   - Smooth transitions with delay timing

4. **TM1637 Display Driver**
   - 4-digit 7-segment display with brightness control
   - Leading zero padding for readability
   - Efficient update mechanism

5. **Blynk Integration**
   - Real-time bidirectional communication
   - Virtual pin mapping for sensors and actuators
   - Mobile app dashboard for remote monitoring

6. **Error Handling**
   - Wi-Fi reconnection logic
   - Blynk connection status monitoring
   - Sensor read validation

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Blynk Cloud Server                      │
│                    (blynk.cloud)                             │
└─────────────────────────────────────────────────────────────┘
                            ▲ │
                            │ │ Wi-Fi
                            │ ▼
┌─────────────────────────────────────────────────────────────┐
│                         ESP32                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              MicroPython Runtime                      │   │
│  │  ┌────────────┐  ┌──────────┐  ┌─────────────┐      │   │
│  │  │ Blynk Lib  │  │ TM1637   │  │ Servo PWM   │      │   │
│  │  │            │  │ Driver   │  │ Control     │      │   │
│  │  └────────────┘  └──────────┘  └─────────────┘      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │         Main Control Logic                    │   │   │
│  │  │  - Auto/Manual Mode Switching                 │   │   │
│  │  │  - IR Detection Handler                       │   │   │
│  │  │  - Counter Management                         │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────┐    ┌─────────┐    ┌────────┐    ┌─────────┐
    │   IR   │    │  Servo  │    │ TM1637 │    │  Blynk  │
    │ Sensor │    │  Motor  │    │Display │    │   App   │
    └────────┘    └─────────┘    └────────┘    └─────────┘
```

## Code Structure

```
lab3-iot-blynk-ir-servo/
├── main.py              # Main control logic and hardware integration
├── BlynkLib.py          # Blynk library for MicroPython
├── tm1637.py            # TM1637 display driver
├── README.md            # This documentation file
└── screenshot/          # Evidence and documentation images
    ├── wiring_setup.png
    ├── component_setup.jpg
    ├── blynk_dashboard.png
    ├── task1_ir_status.png
    ├── task2_servo_control.gif
    ├── task3_auto_gate.gif
    ├── task4_display_sync.gif
    └── task5_manual_override.gif
```

**Main Components in `main.py`:**

- Wi-Fi connection setup
- Blynk initialization and connection
- IR sensor reading function
- Servo motor control with PWM
- TM1637 display update function
- Virtual pin handlers (V0, V1, V2, V3)
- Automatic gate control logic
- Manual override mode handling
- Main event loop

## Troubleshooting

### Common Issues

1. **ESP32 won't connect to Blynk**
   - Verify Auth Token is correct (check email)
   - Ensure Wi-Fi credentials are correct
   - Check if ESP32 is connected to Wi-Fi (serial monitor)
   - Verify Blynk server is accessible (blynk.cloud)

2. **Servo not moving**
   - Check power supply (servo needs 5V, not 3.3V)
   - Verify PWM signal wire connection to GPIO14
   - Test with manual slider control first
   - Check servo duty cycle values (26-128 for SG90)

3. **IR sensor not detecting**
   - Adjust sensor sensitivity potentiometer
   - Check if sensor LED lights up when object is near
   - Verify sensor output is connected to GPIO13
   - Test sensor output with multimeter (should be LOW when detected)

4. **TM1637 display not showing numbers**
   - Check CLK and DIO connections (GPIO18, GPIO19)
   - Verify power supply (3.3V or 5V depending on module)
   - Test with simple display code first
   - Adjust brightness level in code

5. **Counter not incrementing**
   - Check if automatic mode is enabled (switch OFF on Blynk)
   - Verify IR sensor is working
   - Add debug print statements to detection handler
   - Check if `detection_count` variable is being updated

6. **Blynk widgets not updating**
   - Ensure `blynk.run()` is called in main loop
   - Check virtual pin numbers match widget configuration
   - Verify ESP32 is connected to Blynk (check app status)
   - Add delay between `blynk.run()` calls (recommended 50-100ms)
