# Unitree G1 Robot Controller - Complete Integration Guide

An integrated controller for independently controlling the lower body (loco) and upper body (arm) of the Unitree G1 humanoid robot. It combines WebRTC-based real-time communication (AND) with the robot control system (GERRI) to provide reliable remote control.

**Last Updated**: 2025-10-10
**Status**: Loco + Arm Integration Complete

---

## Table of Contents

1. [System Overview](#-system-overview)
2. [Installation](#-installation)
3. [File Structure](#-file-structure)
4. [Control Features](#-control-features)
5. [Arm Actions Complete Guide](#-arm-actions-complete-guide)
6. [Usage](#-usage)
7. [Build Guide](#-build-guide)
8. [Troubleshooting](#-troubleshooting)
9. [References](#-references)

---

## System Overview

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      Remote Client                          │
│                  (Web Browser / Mobile App)                 │
└────────────────────────┬────────────────────────────────────┘
                         │ WebRTC
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              AdaptiveNetworkDaemon (AND)                    │
│         (Network Communication & Media Streaming)           │
└────────────────────────┬────────────────────────────────────┘
                         │ pubsub (pypubsub)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  G1BaseController                           │
│         (Message Routing & Joystick Mapping)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  G1SubController                            │
│         (Unified Loco + Arm Control Interface)              │
└─────────────────┬──────────────────┬────────────────────────┘
                  │                  │
         ┌────────▼────────┐  ┌──────▼──────────┐
         │  G1LocoBridge   │  │  G1ArmBridge    │
         │  (Loco Control) │  │  (Arm Control)  │
         └────────┬────────┘  └──────┬──────────┘
                  │ ctypes           │ ctypes
         ┌────────▼────────┐  ┌──────▼──────────┐
         │ libg1_loco_     │  │ libg1_arm_      │
         │ wrapper.so      │  │ wrapper.so      │
         └────────┬────────┘  └──────┬──────────┘
                  │                  │
                  └────────┬─────────┘
                           ↓
                   ┌───────────────┐
                   │  Unitree SDK2  │
                   │ (ChannelFactory)│
                   └───────┬────────┘
                           │ DDS/Ethernet
                           ↓
                    ┌──────────────┐
                    │  Unitree G1  │
                    │    Robot     │
                    └──────────────┘
```

### Core Concepts

#### ChannelFactory Singleton Pattern
The Unitree SDK's **ChannelFactory** is implemented as a singleton:
- `ChannelFactory::Instance()->Init()` can only be called **once**
- Loco and arm clients **share the same ChannelFactory instance**
- **Solution**: Initialize only in loco wrapper, arm wrapper uses existing instance

#### Integrated Control Flow
1. **Remote Client** → Sends joystick input via WebRTC
2. **AND** → Broadcasts messages via pubsub
3. **G1BaseController** → Joystick mapping and routing
4. **G1SubController** → Calls loco_bridge/arm_bridge
5. **C++ Wrappers** → Executes Unitree SDK functions
6. **Robot** → Receives and executes commands via DDS communication

---

## Installation

### 1. Prerequisites

- **OS**: Ubuntu 20.04 / 22.04 (ARM64 or x86_64)
- **Python**: 3.8 or higher
- **CMake**: 3.10 or higher
- **Compiler**: g++ with C++17 support
- **Unitree SDK2**: Official G1 SDK

### 2. Install Unitree SDK2
```bash
# Download SDK
mkdir ~/dev
cd ~/dev
git clone https://github.com/unitreerobotics/unitree_sdk2.git

# Build SDK
cd unitree_sdk2
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 3. Install Python Dependencies
```bash
cd ~/dev
git clone https://github.com/keti-ai/and_gerri.git # NEED ID and TOKEN
cd and_gerri
sudo chmod 777 install.sh
bash install.sh
```

### 4. Set Environment Variables
```bash
# Add to .bashrc
export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/lib/aarch64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/thirdparty/lib/aarch64:$LD_LIBRARY_PATH

# Apply
source ~/.bashrc
```

### 5. Build C++ Wrappers
```bash
cd cpp_wrapper
mkdir build && cd build
cmake ..
make -j$(nproc)

# Verify creation
ls -lh ../libg1_loco_wrapper.so  # 5.3 MB
ls -lh ../libg1_arm_wrapper.so   # 5.2 MB
```

For detailed build instructions, see [Build Guide](#-build-guide)

---

## File Structure
```
unitree_g1/
├── README.md                    # This integration guide
├── g1_robot.py                  # Main entry point
├── g1_config.py                 # Configuration file
├── g1_base_controller.py        # Upper controller (message routing, joystick mapping)
├── g1_sub_controller.py         # Sub controller (integrated loco + arm control)
├── g1_loco_bridge.py            # Loco Python-C++ bridge
├── g1_arm_bridge.py             # Arm Python-C++ bridge
└── cpp_wrapper/
    ├── CMakeLists.txt           # CMake build configuration
    ├── g1_loco_wrapper.h        # Loco C interface header
    ├── g1_loco_wrapper.cpp      # Loco C++ SDK wrapper implementation
    ├── libg1_loco_wrapper.so    # Loco shared library
    ├── g1_arm_wrapper.h         # Arm C interface header
    ├── g1_arm_wrapper.cpp       # Arm C++ SDK wrapper implementation
    └── libg1_arm_wrapper.so     # Arm shared library
```

### File Descriptions

| File | Role | Key Functions |
|------|------|---------------|
| `g1_robot.py` | Main program | AND/GERRI initialization, process management |
| `g1_config.py` | Configuration management | Robot info, camera, audio settings |
| `g1_base_controller.py` | Message processing | Joystick input mapping (loco + arm), message routing |
| `g1_sub_controller.py` | Integrated robot control | Movement, posture, 16 arm actions control API |
| `g1_loco_bridge.py` | Loco bridge | Loco C++ calls via Python ctypes |
| `g1_arm_bridge.py` | Arm bridge | Arm C++ calls via Python ctypes |
| `g1_loco_wrapper.cpp` | Loco SDK wrapper | Wraps Unitree Loco SDK with C interface |
| `g1_arm_wrapper.cpp` | Arm SDK wrapper | Wraps Unitree Arm SDK with C interface |

---

## Control Features

### Loco (Lower Body) Joystick Mapping

| Input | Description | Function | Shortcut |
|-------|-------------|----------|----------|
| **axes[1] = -1** | Forward | `move_forward()` | #w |
| **axes[1] = 1** | Backward | `move_backward()` | #s |
| **axes[0] = -1** | Move left | `move_left()` | #a |
| **axes[0] = 1** | Move right | `move_right()` | #d |
| **buttons[1]** | Turn right | `turn_right()` | #e |
| **buttons[2]** | Turn left | `turn_left()` | #q |
| **buttons[3]** | Stop | `stop()` | #r |
| **buttons[0]** | Enable motion | `enable_motion()` | #space |
| **buttons[4]** | Sit down | `sit_down()` | #z |
| **buttons[5]** | Stand up | `stand_up()` | #c |
| **buttons[6]** | FSM ID 1 | `set_fsm_id(1)` | #1 |
| **buttons[7]** | FSM ID 4 | `set_fsm_id(4)` | #3 |
| **buttons[8]** | FSM ID 500 | `set_fsm_id(500)` | #6 |
| **buttons[9]** | FSM ID 801 | `set_fsm_id(801)` | #7 |

### Arm (Upper Body) Joystick Mapping

#### Active Mappings (10)

| Input | Description | Function | Shortcut |
|-------|-------------|----------|----------|
| **buttons[10]** | Wave | `arm_wave()` | #h |
| **buttons[11]** | Clap | `arm_clap()` | #j |
| **buttons[12]** | Heart | `arm_heart()` | #k |
| **buttons[13]** | Hug | `arm_hug()` | #l |
| **buttons[14]** | Hands up | `arm_hands_up()` | |
| **buttons[15]** | High five | `arm_high_five()` | |
| **axes[2] = 1** | Reject | `arm_reject()` | |
| **axes[2] = -1** | Shake hand | `arm_shake_hand()` | |
| **axes[3] = 1** | Face wave | `arm_face_wave()` | |
| **axes[3] = -1** | X-ray pose | `arm_x_ray()` | |

#### Code-Only Mappings (6)

Documented as comments in `g1_base_controller.py`:
```python
# ========== ARM ADDITIONAL ACTIONS (Code only) ==========
# ('buttons', 16, 1): ('Arm Two Hand Kiss', lambda: self.sub_controller.arm_two_hand_kiss()),
# ('buttons', 17, 1): ('Arm Left Kiss', lambda: self.sub_controller.arm_left_kiss()),
# ('buttons', 18, 1): ('Arm Right Kiss', lambda: self.sub_controller.arm_right_kiss()),
# ('buttons', 19, 1): ('Arm Right Heart', lambda: self.sub_controller.arm_right_heart()),
# ('buttons', 20, 1): ('Arm Right Hand Up', lambda: self.sub_controller.arm_right_hand_up()),
# ('buttons', 21, 1): ('Arm Release', lambda: self.sub_controller.arm_release()),
```

---

## Arm Actions Complete Guide

### Complete List of 16 Arm Actions

| ID | Action Name | Method | Mapping | Description |
|----|-------------|--------|---------|-------------|
| 11 | two_hand_kiss | `arm_two_hand_kiss()` | Code | Two-hand kiss |
| 12 | left_kiss | `arm_left_kiss()` | Code | Left hand kiss |
| 13 | right_kiss | `arm_right_kiss()` | Code | Right hand kiss |
| 15 | hands_up | `arm_hands_up()` | buttons[14] | Both hands up |
| 17 | clap | `arm_clap()` | buttons[11] | Clap |
| 18 | high_five | `arm_high_five()` | buttons[15] | High five |
| 19 | hug | `arm_hug()` | buttons[13] | Hug |
| 20 | heart | `arm_heart()` | buttons[12] | Heart |
| 21 | right_heart | `arm_right_heart()` | Code | Right hand heart |
| 22 | reject | `arm_reject()` | axes[2]=1 | Reject |
| 23 | right_hand_up | `arm_right_hand_up()` | Code | Right hand up |
| 24 | x_ray | `arm_x_ray()` | axes[3]=-1 | X-ray pose |
| 25 | face_wave | `arm_face_wave()` | axes[3]=1 | Wave in front of face |
| 26 | high_wave | `arm_wave()` | buttons[10] | High wave |
| 27 | shake_hand | `arm_shake_hand()` | axes[2]=-1 | Shake hand |
| 99 | release_arm | `arm_release()` | Code | Release arm |

### FSM State Requirements

Arm actions only work in specific FSM states:

- **FSM 500** (Recommended - supports all modes)
- **FSM 501**
- **FSM 801** (only in mode 0, 3)
```python
# Check and set FSM
code, fsm_id = controller.get_fsm_id()
if fsm_id not in [500, 501, 801]:
    print(f"Current FSM: {fsm_id}")
    controller.set_fsm_id(500)
    time.sleep(2)  # Wait for FSM transition
    print("FSM set to 500 - ready for arm actions")
```

---

## Usage

### 1. Modify Configuration File

Modify robot info and camera/audio settings in `g1_config.py`:
```python
ROBOT_INFO = {
    "id": "unitree_g1",
    "model": "unitree_g1",
    "category": "sample",
    "api_key": "your_api_key_here"
}

VIDEO_INFO = {
    "front_cam": {"source": 0, "width": 1920, "height": 1080},
}

AUDIO_INFO = {
    "audio": {"input": "default", "output": "default"},
}
```

### 2. Run the Robot
```bash
# Run in environment connected to robot
python3 g1_robot.py
```

### 3. Remote Control via Joystick

Connect to the robot via web browser or mobile app:
```bash
# Loco control
axes[1] = -1   # Forward
axes[0] = -1   # Move left
buttons[1]     # Turn right
buttons[3]     # Stop

# Arm control
buttons[10]    # Wave
buttons[11]    # Clap
buttons[12]    # Heart
axes[2] = 1    # Reject
```

### 4. Programming API

#### Loco (Lower Body) Control
```python
from gerri.robot.examples.unitree_g1.g1_sub_controller import G1SubController

controller = G1SubController()
controller.connect()

# Basic movement
controller.move_forward()      # 0.3 m/s forward
controller.move_backward()     # 0.3 m/s backward
controller.move_left()         # Move left
controller.move_right()        # Move right
controller.turn_left()         # 0.5 rad/s turn left
controller.turn_right()        # 0.5 rad/s turn right
controller.stop()              # Stop

# Posture control
controller.enable_motion()     # Start robot
controller.stand_up()          # Stand up
controller.sit_down()          # Sit down

# Direct velocity setting
controller.set_velocity(vx, vy, omega, duration)

# FSM control
controller.set_fsm_id(500)
code, fsm_id = controller.get_fsm_id()
```

#### Arm (Upper Body) Control
```python
# Joystick-mapped actions (10)
controller.arm_wave()           # buttons[10] - Wave
controller.arm_clap()           # buttons[11] - Clap
controller.arm_heart()          # buttons[12] - Heart
controller.arm_hug()            # buttons[13] - Hug
controller.arm_hands_up()       # buttons[14] - Hands up
controller.arm_high_five()      # buttons[15] - High five
controller.arm_reject()         # axes[2]=1 - Reject
controller.arm_shake_hand()     # axes[2]=-1 - Shake hand
controller.arm_face_wave()      # axes[3]=1 - Face wave
controller.arm_x_ray()          # axes[3]=-1 - X-ray

# Code-only actions (6)
controller.arm_two_hand_kiss()
controller.arm_left_kiss()
controller.arm_right_kiss()
controller.arm_right_heart()
controller.arm_right_hand_up()
controller.arm_release()

# Generic method
controller.arm_action("high_wave")
controller.arm_action("clap")
```

#### Simultaneous Control (Loco + Arm)

Lower body and upper body can be **controlled independently and simultaneously**:
```python
# Walk forward while waving
controller.move_forward()
time.sleep(0.5)
controller.arm_wave()

# Turn while clapping
controller.turn_left()
time.sleep(0.5)
controller.arm_clap()

# Walk while making heart
controller.move_forward()
time.sleep(1)
controller.arm_heart()
time.sleep(3)
controller.stop()
```

### 5. Complete Example
```python
#!/usr/bin/env python3
import time
from gerri.robot.examples.unitree_g1.g1_sub_controller import G1SubController

# Create and connect controller
controller = G1SubController()
controller.connect()

# 1. Start robot
controller.enable_motion()
time.sleep(2)
controller.stand_up()
time.sleep(3)

# 2. Check and set FSM state
code, fsm_id = controller.get_fsm_id()
print(f"Current FSM ID: {fsm_id}")

if fsm_id not in [500, 501, 801]:
    print("Setting FSM to 500...")
    controller.set_fsm_id(500)
    time.sleep(2)

# 3. Move forward and wave
print("Moving forward and waving...")
controller.move_forward()
time.sleep(1)
controller.arm_wave()
time.sleep(3)
controller.stop()

# 4. Clap
print("Clapping...")
controller.arm_clap()
time.sleep(3)

# 5. Turn and make heart
print("Turning and making heart...")
controller.turn_left()
time.sleep(1)
controller.arm_heart()
time.sleep(3)
controller.stop()

# 6. Hug pose
print("Hugging...")
controller.arm_hug()
time.sleep(3)

# 7. Disconnect
controller.disconnect()
print("Done!")
```

---

## Build Guide

### Building C++ Wrappers

#### Method 1: Quick Rebuild
```bash
cd cpp_wrapper/build
make clean
make -j$(nproc)
```

#### Method 2: Clean Build
```bash
cd cpp_wrapper
rm -rf build
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### Modify CMake Configuration

Verify SDK path in `cpp_wrapper/CMakeLists.txt`:
```cmake
set(UNITREE_SDK_PATH "/home/tom2025orin006/dev/unitree_sdk2")
```

Modify to match your actual SDK path.

### Verify Build
```bash
# Verify library creation
ls -lh cpp_wrapper/libg1_loco_wrapper.so  # 5.3 MB
ls -lh cpp_wrapper/libg1_arm_wrapper.so   # 5.2 MB

# Check dependencies
ldd cpp_wrapper/libg1_loco_wrapper.so
ldd cpp_wrapper/libg1_arm_wrapper.so

# Test loading in Python
python3 -c "import ctypes; lib = ctypes.CDLL('./cpp_wrapper/libg1_loco_wrapper.so'); print('Loco OK')"
python3 -c "import ctypes; lib = ctypes.CDLL('./cpp_wrapper/libg1_arm_wrapper.so'); print('Arm OK')"
```

### Example Build Output
```
Scanning dependencies of target g1_loco_wrapper
[ 33%] Building CXX object CMakeFiles/g1_loco_wrapper.dir/g1_loco_wrapper.cpp.o
[ 66%] Linking CXX shared library ../libg1_loco_wrapper.so
[ 66%] Built target g1_loco_wrapper

Scanning dependencies of target g1_arm_wrapper
[100%] Building CXX object CMakeFiles/g1_arm_wrapper.dir/g1_arm_wrapper.cpp.o
[100%] Linking CXX shared library ../libg1_arm_wrapper.so
[100%] Built target g1_arm_wrapper

-rwxrwxr-x 1 user user 5.3M libg1_loco_wrapper.so
-rwxrwxr-x 1 user user 5.2M libg1_arm_wrapper.so
```

---

## Troubleshooting

### 1. Library Not Found

**Symptom**:
```
ImportError: libunitree_sdk2.so: cannot open shared object file
```

**Solution**:
```bash
export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/lib/aarch64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/thirdparty/lib/aarch64:$LD_LIBRARY_PATH

# Add permanently to .bashrc
echo 'export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/lib/aarch64:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/thirdparty/lib/aarch64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### 2. ChannelFactory Already Initialized Error

**Symptom**:
```
[ERROR] ChannelFactory already initialized
```

**Cause**: Arm wrapper attempting to reinitialize ChannelFactory

**Solution**: Remove `ChannelFactory::Init()` from `g1_arm_wrapper.cpp` (already applied)

### 3. CMake Cannot Find SDK

**Symptom**:
```
CMake Error: Could not find unitree SDK headers
```

**Solution**:
Modify SDK path in `CMakeLists.txt` to actual path:
```cmake
set(UNITREE_SDK_PATH "/your/actual/path/to/unitree_sdk2")
```

### 4. Robot Connection Failed

**Symptom**:
```
[ERROR] Connection failed: Failed to create loco client
```

**Checklist**:
1. Verify robot power is on
2. Check network interface (`ip link` or `ifconfig`)
3. Modify network interface in `g1_sub_controller.py`:
```python
   # In __init__ method
   network_interface = "eth0"  # Change to actual interface
```

### 5. Arm Action Not Executing

**Checklist**:

1. **Check FSM state**:
```python
   code, fsm_id = controller.get_fsm_id()
   print(f"Current FSM ID: {fsm_id}")

   if fsm_id not in [500, 501, 801]:
       controller.set_fsm_id(500)
       time.sleep(2)
```

2. **Verify robot is standing**:
```python
   controller.stand_up()
   time.sleep(3)
```

3. **Check error codes**:
   - `-5`: Arm SDK error
   - `-6`: Robot is holding something
   - `-7`: Invalid action ID
   - `-8`: Invalid FSM state

4. **Debugging**:
```python
   success, msg = controller.arm_bridge.execute_action_by_name("high_wave")
   if not success:
       print(f"Failed: {msg}")
```

### 6. libg1_arm_wrapper.so Not Found

**Solution**:
```bash
cd cpp_wrapper/build
cmake ..
make -j$(nproc)
ls ../libg1_arm_wrapper.so  # Verify creation
```

### 7. Compilation Errors

**C++17 support error**:
```bash
# Check g++ version
g++ --version  # Requires 7.0 or higher

# Upgrade
sudo apt update
sudo apt install g++-9
```

### 8. DDS Library Error

**Symptom**:
```
CMake Error: Could not find DDS libraries
```

**Solution**:
Check architecture and modify path:
```bash
# Check architecture
uname -m
# x86_64 → lib/x86_64
# aarch64 → lib/aarch64
```

Modify `CMakeLists.txt` for your architecture:
```cmake
set(ARCH "aarch64")  # or "x86_64"
```

### 9. Robot Not Responding to Commands

**Checklist**:

1. **Check FSM state**:
```python
   code, fsm_id = controller.get_fsm_id()
   print(f"Current FSM ID: {fsm_id}")
```

2. **Activate robot**:
```python
   controller.enable_motion()
   time.sleep(2)
   controller.stand_up()
   time.sleep(3)
```

3. **Check return codes**:
   - `0`: Success
   - `3104`: Robot not ready
   - `-1`: General error

### 10. Initialization Order Issues

**Important**: Always initialize in **loco → arm** order:
```python
# Correct order
self.loco_bridge = G1LocoBridge("eth0")
self.loco_bridge.connect()  # Initializes ChannelFactory

self.arm_bridge = G1ArmBridge("eth0")
self.arm_bridge.connect()   # Uses existing ChannelFactory

# Wrong order
self.arm_bridge = G1ArmBridge("eth0")
self.arm_bridge.connect()   # ChannelFactory not initialized!

self.loco_bridge = G1LocoBridge("eth0")
self.loco_bridge.connect()  # May cause error
```

---

## References

### Official Documentation
- [Unitree SDK2 Official Documentation](https://github.com/unitreerobotics/unitree_sdk2)
- [Unitree G1 User Manual](https://www.unitree.com/g1)
- [DDS Communication Protocol](https://www.dds-foundation.org/)

### Key Concepts
- **ChannelFactory Singleton**: Core communication manager of Unitree SDK
- **FSM (Finite State Machine)**: Robot state management system
- **DDS (Data Distribution Service)**: Robot communication protocol
- **WebRTC**: Real-time remote control communication
- **pypubsub**: Python publish-subscribe messaging

### Project Structure
- **AND (Adaptive Network Daemon)**: WebRTC-based network layer
- **GERRI**: Robot control system
- **ctypes**: Python-C++ interface
- **CMake**: C++ build system

---

## Integration Summary

### Implemented Features

| Category | Item | Status |
|----------|------|--------|
| **Loco Control** | Movement, rotation, stop | ✅ |
| **Loco Posture** | Sit, stand, FSM control | ✅ |
| **Arm Actions** | All 16 implemented | ✅ |
| **Joystick Arm** | 10 mapped (6 buttons + 4 axes) | ✅ |
| **Code Arm** | 6 additional methods | ✅ |
| **C++ Wrappers** | Loco + arm build complete | ✅ |
| **ChannelFactory** | Singleton conflict resolved | ✅ |
| **Simultaneous Control** | Independent loco + arm control | ✅ |
