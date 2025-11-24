# Unitree G1 Robot Controller - 완전 통합 가이드

Unitree G1 humanoid robot의 하체(loco)와 상체(arm)를 독립적으로 제어하는 통합 컨트롤러입니다. WebRTC 기반 실시간 통신(AND)과 로봇 제어 시스템(GERRI)을 결합하여 안정적인 원격 제어를 제공합니다.

**최종 업데이트**: 2025-10-10
**상태**: Loco + Arm 통합 완료

---

## 목차

1. [시스템 개요](#-시스템-개요)
2. [설치 방법](#-설치-방법)
3. [파일 구조](#-파일-구조)
4. [제어 기능](#-제어-기능)
5. [Arm Actions 완전 가이드](#-arm-actions-완전-가이드)
6. [사용 방법](#-사용-방법)
7. [빌드 가이드](#-빌드-가이드)
8. [문제 해결](#-문제-해결)
9. [참고 자료](#-참고-자료)

---

## 시스템 개요

### 아키텍처

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
         │  (Loco 제어)     │  │  (Arm 제어)      │
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

### 핵심 개념

#### ChannelFactory 싱글톤 패턴
Unitree SDK의 **ChannelFactory**는 싱글톤으로 구현되어 있습니다:
- `ChannelFactory::Instance()->Init()`는 **단 한 번만** 호출 가능
- loco와 arm 클라이언트는 **같은 ChannelFactory 인스턴스를 공유**
- **해결 방법**: loco wrapper에서만 초기화, arm wrapper는 기존 인스턴스 사용

#### 통합 제어 흐름
1. **Remote Client** → WebRTC로 조이스틱 입력 전송
2. **AND** → pubsub으로 메시지 브로드캐스트
3. **G1BaseController** → 조이스틱 매핑 및 라우팅
4. **G1SubController** → loco_bridge/arm_bridge 호출
5. **C++ Wrappers** → Unitree SDK 함수 실행
6. **로봇** → DDS 통신으로 명령 수신 및 실행

---

## 설치 방법

### 1. 사전 요구사항

- **OS**: Ubuntu 20.04 / 22.04 (ARM64 또는 x86_64)
- **Python**: 3.8 이상
- **CMake**: 3.10 이상
- **Compiler**: g++ with C++17 support
- **Unitree SDK2**: 공식 G1 SDK

### 2. Unitree SDK2 설치

```bash
# SDK 다운로드
mkdir ~/dev
cd ~/dev
git clone https://github.com/unitreerobotics/unitree_sdk2.git

# SDK 빌드
cd unitree_sdk2
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 3. Python 의존성 설치

```bash
cd ~/dev
git clone https://github.com/keti-ai/and_gerri.git # NEED ID and TOKEN
cd and_gerri
sudo chmod 777 install.sh
bash install.sh
```

### 4. 환경 변수 설정

```bash
# .bashrc에 추가
export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/lib/aarch64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/thirdparty/lib/aarch64:$LD_LIBRARY_PATH

# 적용
source ~/.bashrc
```

### 5. C++ Wrapper 빌드

```bash
cd cpp_wrapper
mkdir build && cd build
cmake ..
make -j$(nproc)

# 생성 확인
ls -lh ../libg1_loco_wrapper.so  # 5.3 MB
ls -lh ../libg1_arm_wrapper.so   # 5.2 MB
```

자세한 빌드 방법은 [빌드 가이드](#-빌드-가이드) 참조

---

## 파일 구조

```
unitree_g1/
├── README.md                    # 이 통합 가이드
├── g1_robot.py                  # 메인 진입점
├── g1_config.py                 # 설정 파일
├── g1_base_controller.py        # 상위 컨트롤러 (메시지 라우팅, 조이스틱 매핑)
├── g1_sub_controller.py         # 하위 컨트롤러 (통합 loco + arm 제어)
├── g1_loco_bridge.py            # Loco Python-C++ 브릿지
├── g1_arm_bridge.py             # Arm Python-C++ 브릿지
└── cpp_wrapper/
    ├── CMakeLists.txt           # CMake 빌드 설정
    ├── g1_loco_wrapper.h        # Loco C 인터페이스 헤더
    ├── g1_loco_wrapper.cpp      # Loco C++ SDK 래퍼 구현
    ├── libg1_loco_wrapper.so    # Loco 공유 라이브러리
    ├── g1_arm_wrapper.h         # Arm C 인터페이스 헤더
    ├── g1_arm_wrapper.cpp       # Arm C++ SDK 래퍼 구현
    └── libg1_arm_wrapper.so     # Arm 공유 라이브러리
```

### 파일 설명

| 파일 | 역할 | 주요 기능 |
|------|------|-----------|
| `g1_robot.py` | 메인 프로그램 | AND/GERRI 초기화, 프로세스 유지 |
| `g1_config.py` | 설정 관리 | 로봇 정보, 카메라, 오디오 설정 |
| `g1_base_controller.py` | 메시지 처리 | 조이스틱 입력 매핑 (loco + arm), 메시지 라우팅 |
| `g1_sub_controller.py` | 통합 로봇 제어 | 이동, 자세, 16개 arm actions 제어 API |
| `g1_loco_bridge.py` | Loco 브릿지 | Python ctypes를 통한 loco C++ 호출 |
| `g1_arm_bridge.py` | Arm 브릿지 | Python ctypes를 통한 arm C++ 호출 |
| `g1_loco_wrapper.cpp` | Loco SDK 래퍼 | Unitree Loco SDK를 C 인터페이스로 래핑 |
| `g1_arm_wrapper.cpp` | Arm SDK 래퍼 | Unitree Arm SDK를 C 인터페이스로 래핑 |

---

## 제어 기능

### Loco (하체) 조이스틱 매핑

| 입력 | 설명 | 함수 | 단축키 |
|------|------|------|--------|
| **axes[1] = -1** | 전진 | `move_forward()` | #w |
| **axes[1] = 1** | 후진 | `move_backward()` | #s |
| **axes[0] = -1** | 좌측 이동 | `move_left()` | #a |
| **axes[0] = 1** | 우측 이동 | `move_right()` | #d |
| **buttons[1]** | 우회전 | `turn_right()` | #e |
| **buttons[2]** | 좌회전 | `turn_left()` | #q |
| **buttons[3]** | 정지 | `stop()` | #r |
| **buttons[0]** | 모션 활성화 | `enable_motion()` | #space |
| **buttons[4]** | 앉기 | `sit_down()` | #z |
| **buttons[5]** | 일어서기 | `stand_up()` | #c |
| **buttons[6]** | FSM ID 1 | `set_fsm_id(1)` | #1 |
| **buttons[7]** | FSM ID 4 | `set_fsm_id(4)` | #3 |
| **buttons[8]** | FSM ID 500 | `set_fsm_id(500)` | #6 |
| **buttons[9]** | FSM ID 801 | `set_fsm_id(801)` | #7 |

### Arm (상체) 조이스틱 매핑

#### 활성화된 매핑 (10개)

| 입력 | 설명 | 함수 | 단축키 |
|------|------|------|--------|
| **buttons[10]** | 손 흔들기 | `arm_wave()` | #h |
| **buttons[11]** | 박수 | `arm_clap()` | #j |
| **buttons[12]** | 하트 | `arm_heart()` | #k |
| **buttons[13]** | 포옹 | `arm_hug()` | #l |
| **buttons[14]** | 양손 들기 | `arm_hands_up()` | |
| **buttons[15]** | 하이파이브 | `arm_high_five()` | |
| **axes[2] = 1** | 거절 | `arm_reject()` | |
| **axes[2] = -1** | 악수 | `arm_shake_hand()` | |
| **axes[3] = 1** | 얼굴 앞 손 흔들기 | `arm_face_wave()` | |
| **axes[3] = -1** | X-ray 포즈 | `arm_x_ray()` | |

#### 코드 전용 매핑 (6개)

주석으로 `g1_base_controller.py`에 문서화되어 있음:

```python
# ========== ARM 추가 액션 (코드로만 사용 가능) ==========
# ('buttons', 16, 1): ('Arm Two Hand Kiss', lambda: self.sub_controller.arm_two_hand_kiss()),
# ('buttons', 17, 1): ('Arm Left Kiss', lambda: self.sub_controller.arm_left_kiss()),
# ('buttons', 18, 1): ('Arm Right Kiss', lambda: self.sub_controller.arm_right_kiss()),
# ('buttons', 19, 1): ('Arm Right Heart', lambda: self.sub_controller.arm_right_heart()),
# ('buttons', 20, 1): ('Arm Right Hand Up', lambda: self.sub_controller.arm_right_hand_up()),
# ('buttons', 21, 1): ('Arm Release', lambda: self.sub_controller.arm_release()),
```

---

## 🦾 Arm Actions 완전 가이드

### 전체 16개 Arm Actions 목록

| ID | Action Name | Method | 매핑 방법 | 설명 |
|----|-------------|--------|----------|------|
| 11 | two_hand_kiss | `arm_two_hand_kiss()` | 코드 | 양손 키스 |
| 12 | left_kiss | `arm_left_kiss()` | 코드 | 왼손 키스 |
| 13 | right_kiss | `arm_right_kiss()` | 코드 | 오른손 키스 |
| 15 | hands_up | `arm_hands_up()` | buttons[14] | 양손 들기 |
| 17 | clap | `arm_clap()` | buttons[11] | 박수 |
| 18 | high_five | `arm_high_five()` | buttons[15] | 하이파이브 |
| 19 | hug | `arm_hug()` | buttons[13] | 포옹 |
| 20 | heart | `arm_heart()` | buttons[12] | 하트 |
| 21 | right_heart | `arm_right_heart()` | 코드 | 오른손 하트 |
| 22 | reject | `arm_reject()` | axes[2]=1 | 거절 |
| 23 | right_hand_up | `arm_right_hand_up()` | 코드 | 오른손 들기 |
| 24 | x_ray | `arm_x_ray()` | axes[3]=-1 | X-ray 포즈 |
| 25 | face_wave | `arm_face_wave()` | axes[3]=1 | 얼굴 앞 손 흔들기 |
| 26 | high_wave | `arm_wave()` | buttons[10] | 높이 손 흔들기 |
| 27 | shake_hand | `arm_shake_hand()` | axes[2]=-1 | 악수 |
| 99 | release_arm | `arm_release()` | 코드 | 팔 해제 |

### FSM 상태 요구사항

Arm action은 특정 FSM 상태에서만 동작합니다:

- **FSM 500** (권장 - 모든 모드 지원)
- **FSM 501**
- **FSM 801** (mode 0, 3에서만)

```python
# FSM 확인 및 설정
code, fsm_id = controller.get_fsm_id()
if fsm_id not in [500, 501, 801]:
    print(f"Current FSM: {fsm_id}")
    controller.set_fsm_id(500)
    time.sleep(2)  # FSM 전환 대기
    print("FSM set to 500 - ready for arm actions")
```

---

## 사용 방법

### 1. 설정 파일 수정

`g1_config.py`에서 로봇 정보와 카메라/오디오 설정을 수정하세요:

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

### 2. 로봇 실행

```bash
# 로봇이 연결된 환경에서 실행
python3 g1_robot.py
```

### 3. 조이스틱으로 원격 제어

웹 브라우저나 모바일 앱에서 로봇에 접속하여 제어:

```bash
# Loco 제어
axes[1] = -1   # 전진
axes[0] = -1   # 좌측 이동
buttons[1]     # 우회전
buttons[3]     # 정지

# Arm 제어
buttons[10]    # 손 흔들기
buttons[11]    # 박수
buttons[12]    # 하트
axes[2] = 1    # 거절
```

### 4. 프로그래밍 API

#### Loco (하체) 제어

```python
from gerri.robot.examples.unitree_g1.g1_sub_controller import G1SubController

controller = G1SubController()
controller.connect()

# 기본 이동
controller.move_forward()      # 0.3 m/s 전진
controller.move_backward()     # 0.3 m/s 후진
controller.move_left()         # 좌측 이동
controller.move_right()        # 우측 이동
controller.turn_left()         # 0.5 rad/s 좌회전
controller.turn_right()        # 0.5 rad/s 우회전
controller.stop()              # 정지

# 자세 제어
controller.enable_motion()     # 로봇 시작
controller.stand_up()          # 일어서기
controller.sit_down()          # 앉기

# 직접 속도 설정
controller.set_velocity(vx, vy, omega, duration)

# FSM 제어
controller.set_fsm_id(500)
code, fsm_id = controller.get_fsm_id()
```

#### Arm (상체) 제어

```python
# 조이스틱 매핑된 동작 (10개)
controller.arm_wave()           # buttons[10] - 손 흔들기
controller.arm_clap()           # buttons[11] - 박수
controller.arm_heart()          # buttons[12] - 하트
controller.arm_hug()            # buttons[13] - 포옹
controller.arm_hands_up()       # buttons[14] - 양손 들기
controller.arm_high_five()      # buttons[15] - 하이파이브
controller.arm_reject()         # axes[2]=1 - 거절
controller.arm_shake_hand()     # axes[2]=-1 - 악수
controller.arm_face_wave()      # axes[3]=1 - 얼굴 앞 손 흔들기
controller.arm_x_ray()          # axes[3]=-1 - X-ray

# 코드 전용 동작 (6개)
controller.arm_two_hand_kiss()
controller.arm_left_kiss()
controller.arm_right_kiss()
controller.arm_right_heart()
controller.arm_right_hand_up()
controller.arm_release()

# 범용 메소드
controller.arm_action("high_wave")
controller.arm_action("clap")
```

#### 동시 제어 (Loco + Arm)

하체와 상체는 **독립적으로 동시 제어 가능**:

```python
# 전진하면서 손 흔들기
controller.move_forward()
time.sleep(0.5)
controller.arm_wave()

# 회전하면서 박수
controller.turn_left()
time.sleep(0.5)
controller.arm_clap()

# 걷으면서 하트 만들기
controller.move_forward()
time.sleep(1)
controller.arm_heart()
time.sleep(3)
controller.stop()
```

### 5. 완전한 예제

```python
#!/usr/bin/env python3
import time
from gerri.robot.examples.unitree_g1.g1_sub_controller import G1SubController

# 컨트롤러 생성 및 연결
controller = G1SubController()
controller.connect()

# 1. 로봇 시작
controller.enable_motion()
time.sleep(2)
controller.stand_up()
time.sleep(3)

# 2. FSM 상태 확인 및 설정
code, fsm_id = controller.get_fsm_id()
print(f"Current FSM ID: {fsm_id}")

if fsm_id not in [500, 501, 801]:
    print("Setting FSM to 500...")
    controller.set_fsm_id(500)
    time.sleep(2)

# 3. 전진하면서 손 흔들기
print("Moving forward and waving...")
controller.move_forward()
time.sleep(1)
controller.arm_wave()
time.sleep(3)
controller.stop()

# 4. 박수 치기
print("Clapping...")
controller.arm_clap()
time.sleep(3)

# 5. 회전하면서 하트 만들기
print("Turning and making heart...")
controller.turn_left()
time.sleep(1)
controller.arm_heart()
time.sleep(3)
controller.stop()

# 6. 포옹 자세
print("Hugging...")
controller.arm_hug()
time.sleep(3)

# 7. 연결 해제
controller.disconnect()
print("Done!")
```

---

## 빌드 가이드

### C++ Wrapper 빌드

#### 방법 1: 빠른 재빌드

```bash
cd cpp_wrapper/build
make clean
make -j$(nproc)
```

#### 방법 2: 클린 빌드

```bash
cd cpp_wrapper
rm -rf build
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### CMake 설정 수정

`cpp_wrapper/CMakeLists.txt`에서 SDK 경로 확인:

```cmake
set(UNITREE_SDK_PATH "/home/tom2025orin006/dev/unitree_sdk2")
```

실제 SDK 경로에 맞게 수정하세요.

### 빌드 확인

```bash
# 라이브러리 생성 확인
ls -lh cpp_wrapper/libg1_loco_wrapper.so  # 5.3 MB
ls -lh cpp_wrapper/libg1_arm_wrapper.so   # 5.2 MB

# 의존성 확인
ldd cpp_wrapper/libg1_loco_wrapper.so
ldd cpp_wrapper/libg1_arm_wrapper.so

# Python에서 로드 테스트
python3 -c "import ctypes; lib = ctypes.CDLL('./cpp_wrapper/libg1_loco_wrapper.so'); print('Loco OK')"
python3 -c "import ctypes; lib = ctypes.CDLL('./cpp_wrapper/libg1_arm_wrapper.so'); print('Arm OK')"
```

### 빌드 출력 예시

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

## 문제 해결

### 1. 라이브러리를 찾을 수 없음

**증상**:
```
ImportError: libunitree_sdk2.so: cannot open shared object file
```

**해결**:
```bash
export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/lib/aarch64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/thirdparty/lib/aarch64:$LD_LIBRARY_PATH

# .bashrc에 영구 추가
echo 'export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/lib/aarch64:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/home/tom2025orin006/dev/unitree_sdk2/thirdparty/lib/aarch64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### 2. ChannelFactory already initialized 에러

**증상**:
```
[ERROR] ChannelFactory already initialized
```

**원인**: arm wrapper에서 ChannelFactory를 다시 초기화하려고 시도

**해결**: `g1_arm_wrapper.cpp`에서 `ChannelFactory::Init()` 제거 (이미 적용됨)

### 3. CMake SDK를 찾을 수 없음

**증상**:
```
CMake Error: Could not find unitree SDK headers
```

**해결**:
`CMakeLists.txt`에서 SDK 경로를 실제 경로로 수정:
```cmake
set(UNITREE_SDK_PATH "/your/actual/path/to/unitree_sdk2")
```

### 4. 로봇 연결 실패

**증상**:
```
[ERROR] Connection failed: Failed to create loco client
```

**확인사항**:
1. 로봇 전원이 켜져 있는지 확인
2. 네트워크 인터페이스 확인 (`ip link` 또는 `ifconfig`)
3. `g1_sub_controller.py`에서 네트워크 인터페이스 수정:
   ```python
   # __init__ 메소드에서
   network_interface = "eth0"  # 실제 인터페이스로 변경
   ```

### 5. Arm action이 실행되지 않음

**확인사항**:

1. **FSM 상태 확인**:
   ```python
   code, fsm_id = controller.get_fsm_id()
   print(f"Current FSM ID: {fsm_id}")

   if fsm_id not in [500, 501, 801]:
       controller.set_fsm_id(500)
       time.sleep(2)
   ```

2. **로봇이 서있는지 확인**:
   ```python
   controller.stand_up()
   time.sleep(3)
   ```

3. **에러 코드 확인**:
   - `-5`: Arm SDK 오류
   - `-6`: 로봇이 무언가를 잡고 있음
   - `-7`: 잘못된 action ID
   - `-8`: 잘못된 FSM 상태

4. **디버깅**:
   ```python
   success, msg = controller.arm_bridge.execute_action_by_name("high_wave")
   if not success:
       print(f"Failed: {msg}")
   ```

### 6. libg1_arm_wrapper.so를 찾을 수 없음

**해결**:
```bash
cd cpp_wrapper/build
cmake ..
make -j$(nproc)
ls ../libg1_arm_wrapper.so  # 생성 확인
```

### 7. 컴파일 에러

**C++17 지원 에러**:
```bash
# g++ 버전 확인
g++ --version  # 7.0 이상 필요

# 업그레이드
sudo apt update
sudo apt install g++-9
```

### 8. DDS 라이브러리 에러

**증상**:
```
CMake Error: Could not find DDS libraries
```

**해결**:
아키텍처 확인 후 경로 수정:
```bash
# 아키텍처 확인
uname -m
# x86_64 → lib/x86_64
# aarch64 → lib/aarch64
```

`CMakeLists.txt`에서 아키텍처에 맞게 수정:
```cmake
set(ARCH "aarch64")  # 또는 "x86_64"
```

### 9. 로봇이 명령에 반응하지 않음

**확인사항**:

1. **FSM 상태 확인**:
   ```python
   code, fsm_id = controller.get_fsm_id()
   print(f"Current FSM ID: {fsm_id}")
   ```

2. **로봇 활성화**:
   ```python
   controller.enable_motion()
   time.sleep(2)
   controller.stand_up()
   time.sleep(3)
   ```

3. **리턴 코드 확인**:
   - `0`: 성공
   - `3104`: 로봇 준비되지 않음
   - `-1`: 일반 에러

### 10. 초기화 순서 문제

**중요**: 반드시 **loco → arm** 순서로 초기화:

```python
# 올바른 순서
self.loco_bridge = G1LocoBridge("eth0")
self.loco_bridge.connect()  # ChannelFactory 초기화

self.arm_bridge = G1ArmBridge("eth0")
self.arm_bridge.connect()   # 기존 ChannelFactory 사용

# 잘못된 순서
self.arm_bridge = G1ArmBridge("eth0")
self.arm_bridge.connect()   # ChannelFactory 초기화 안 됨!

self.loco_bridge = G1LocoBridge("eth0")
self.loco_bridge.connect()  # 에러 발생 가능
```

---

## 참고 자료

### 공식 문서
- [Unitree SDK2 공식 문서](https://github.com/unitreerobotics/unitree_sdk2)
- [Unitree G1 사용자 매뉴얼](https://www.unitree.com/g1)
- [DDS 통신 프로토콜](https://www.dds-foundation.org/)

### 주요 개념
- **ChannelFactory 싱글톤**: Unitree SDK의 핵심 통신 관리자
- **FSM (Finite State Machine)**: 로봇 상태 관리 시스템
- **DDS (Data Distribution Service)**: 로봇 통신 프로토콜
- **WebRTC**: 실시간 원격 제어 통신
- **pypubsub**: Python publish-subscribe 메시징

### 프로젝트 구조
- **AND (Adaptive Network Daemon)**: WebRTC 기반 네트워크 계층
- **GERRI**: 로봇 제어 시스템
- **ctypes**: Python-C++ 인터페이스
- **CMake**: C++ 빌드 시스템

---

## 통합 완료 요약

### 구현된 기능

| 구분 | 항목 | 상태 |
|------|------|------|
| **Loco 제어** | 이동, 회전, 정지 | ✅ |
| **Loco 자세** | 앉기, 서기, FSM 제어 | ✅ |
| **Arm Actions** | 16개 전체 구현 | ✅ |
| **조이스틱 Arm** | 10개 매핑 (buttons 6 + axes 4) | ✅ |
| **코드 Arm** | 6개 추가 메소드 | ✅ |
| **C++ Wrappers** | loco + arm 빌드 완료 | ✅ |
| **ChannelFactory** | 싱글톤 충돌 해결 | ✅ |
| **동시 제어** | loco + arm 독립 제어 | ✅ |

