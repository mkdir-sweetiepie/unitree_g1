import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(sys.executable), "../..")))

# Create minimal required classes to avoid import issues
class RobotStatus:
    """Minimal RobotStatus implementation"""
    def __init__(self, robot_id, model, category):
        self.robot_id = robot_id
        self.robot_model = model
        self.robot_category = category
        self.pose = {"2d": {"x": 0, "y": 0, "th": 0}}
        self.motion_state = "idle"

import threading
import time
import traceback

# C++ Bridge만 사용
try:
    print("[INFO] Loading C++ Bridge...")
    from g1_cpp_bridge import G1CppBridge
    CPP_BRIDGE_AVAILABLE = True
    print("[SUCCESS] C++ Bridge loaded successfully")
except Exception as e:
    print(f"[ERROR] C++ Bridge failed: {e}")
    print("[ERROR] Cannot operate without C++ Bridge")
    CPP_BRIDGE_AVAILABLE = False


class G1SubController:
    def __init__(self):
        self.robot_controller = None
        self.base_controller = None
        self.status = None
        self._lock = threading.Lock()
        
        # Robot control client
        self.cpp_bridge = None
        
        # Movement parameters
        self.default_velocity = 0.3  # m/s
        self.default_angular_velocity = 0.5  # rad/s
        
        print("[INFO] G1SubController initialized")

    def connect(self):
        """로봇 연결 및 초기화"""
        try:
            # Check if base_controller is set
            if not self.base_controller:
                raise ValueError("base_controller is not set. Cannot initialize status.")

            # Status 초기화
            self.status = RobotStatus(robot_id=self.base_controller.robot_id,
                                      model=self.base_controller.robot_model,
                                      category=self.base_controller.robot_category)
            
            # 로봇 클라이언트 초기화
            self._initialize_robot_client()
            
            # 상태 업데이트 스레드 시작
            threading.Thread(target=self._update_loop, daemon=True).start()
            
            print("[SUCCESS] G1SubController connected successfully")
            
        except Exception as e:
            print(f"[ERROR] Failed to connect G1SubController: {e}")
            traceback.print_exc()

    def _initialize_robot_client(self):
        """로봇 클라이언트 초기화 (C++ Bridge만 사용)"""
        network_interface = "eth0"  # 실제 로봇 연결을 위한 네트워크 인터페이스

        if not CPP_BRIDGE_AVAILABLE:
            print("[ERROR] C++ Bridge not available - robot control disabled")
            return

        try:
            print("[INFO] Initializing C++ Bridge...")
            self.cpp_bridge = G1CppBridge(network_interface)

            if self.cpp_bridge.connect():
                print("[SUCCESS] C++ Bridge connected")
                
                # 기본 기능 테스트
                code, fsm_id = self.cpp_bridge.get_fsm_id()
                if code == 0:
                    print(f"[SUCCESS] C++ Bridge working - FSM ID: {fsm_id}")
                    return
                else:
                    raise RuntimeError(f"FSM test failed with code {code}")
            else:
                raise RuntimeError("Connection failed")

        except Exception as e:
            print(f"[ERROR] C++ Bridge initialization failed: {e}")
            self.cpp_bridge = None

    def _update_loop(self):
        """상태 업데이트 루프"""
        while True:
            try:
                with self._lock:
                    if self.status:
                        # 상태 업데이트 로직 (실제 센서 데이터)
                        self._update_robot_status()
                    
                time.sleep(0.1)  # 10Hz 업데이트
                
            except Exception as e:
                print(f"[WARNING] Status update error: {e}")
                time.sleep(1.0)

    def _update_robot_status(self):
        """로봇 상태 업데이트"""
        try:
            if self.cpp_bridge:
                # C++ Bridge를 통한 실제 상태 조회
                code, fsm_id = self.cpp_bridge.get_fsm_id()
                if code == 0:
                    self.status.motion_state = f"fsm_id_{fsm_id}"
                else:
                    self.status.motion_state = "unknown"
            else:
                # C++ Bridge 없음
                self.status.motion_state = "disconnected"
                
        except Exception as e:
            print(f"[WARNING] Failed to update status: {e}")
            self.status.motion_state = "error"

    def _execute_command(self, command_func, command_name):
        """명령 실행 헬퍼 메소드"""
        try:
            with self._lock:
                if self.cpp_bridge:
                    result = command_func()
                    print(f"[CONTROL] {command_name} executed - result: {result}")
                    return result
                else:
                    print(f"[ERROR] No C++ Bridge connection - {command_name} ignored")
                    return -1
        except Exception as e:
            print(f"[ERROR] {command_name} failed: {e}")
            return -1

    # ========== 기본 이동 제어 메소드들 ==========
    def move_forward(self):
        """전진"""
        return self._execute_command(
            lambda: self.cpp_bridge.move_robot(self.default_velocity, 0, 0),
            "move_forward"
        )

    def move_backward(self):
        """후진"""
        return self._execute_command(
            lambda: self.cpp_bridge.move_robot(-self.default_velocity, 0, 0),
            "move_backward"
        )

    def move_left(self):
        """좌측 이동"""
        return self._execute_command(
            lambda: self.cpp_bridge.move_robot(0, self.default_velocity, 0),
            "move_left"
        )

    def move_right(self):
        """우측 이동"""
        return self._execute_command(
            lambda: self.cpp_bridge.move_robot(0, -self.default_velocity, 0),
            "move_right"
        )

    def turn_left(self):
        """좌회전"""
        return self._execute_command(
            lambda: self.cpp_bridge.move_robot(0, 0, self.default_angular_velocity),
            "turn_left"
        )

    def turn_right(self):
        """우회전"""
        return self._execute_command(
            lambda: self.cpp_bridge.move_robot(0, 0, -self.default_angular_velocity),
            "turn_right"
        )

    def stop(self):
        """정지"""
        return self._execute_command(
            lambda: self.cpp_bridge.stop_move(),
            "stop"
        )

    def stop_motion(self):
        """이동 정지 (stop과 동일)"""
        return self.stop()

    # ========== 자세 제어 메소드들 ==========
    def stand_up(self):
        """일어서기"""
        return self._execute_command(
            lambda: self.cpp_bridge.stand_up(),
            "stand_up"
        )

    def sit_down(self):
        """앉기"""
        return self._execute_command(
            lambda: self.cpp_bridge.sit(),
            "sit_down"
        )

    def enable_motion(self):
        """모션 활성화 (로봇 시작)"""
        return self._execute_command(
            lambda: self.cpp_bridge.start_robot(),
            "enable_motion"
        )

    def squat(self):
        """쪼그려 앉기"""
        return self._execute_command(
            lambda: self.cpp_bridge.squat(),
            "squat"
        )

    def balance_stand(self):
        """밸런스 스탠드"""
        return self._execute_command(
            lambda: self.cpp_bridge.balance_stand(),
            "balance_stand"
        )

    def damp(self):
        """댐핑 모드"""
        return self._execute_command(
            lambda: self.cpp_bridge.damp(),
            "damp"
        )

    def zero_torque(self):
        """제로 토크"""
        return self._execute_command(
            lambda: self.cpp_bridge.zero_torque(),
            "zero_torque"
        )

    def high_stand(self):
        """높은 자세로 서기"""
        return self._execute_command(
            lambda: self.cpp_bridge.high_stand(),
            "high_stand"
        )

    def low_stand(self):
        """낮은 자세로 서기"""
        return self._execute_command(
            lambda: self.cpp_bridge.low_stand(),
            "low_stand"
        )

    # ========== 손 제어 메소드들 ==========
    def wave_hand(self):
        """손 흔들기"""
        return self._execute_command(
            lambda: self.cpp_bridge.wave_hand(),
            "wave_hand"
        )

    def shake_hand(self, stage=-1):
        """악수 동작"""
        return self._execute_command(
            lambda: self.cpp_bridge.shake_hand(stage),
            f"shake_hand(stage={stage})"
        )

    # ========== FSM 및 모드 제어 메소드들 ==========
    def set_fsm_id(self, fsm_id: int):
        """FSM ID 설정"""
        return self._execute_command(
            lambda: self.cpp_bridge.set_fsm_id(fsm_id),
            f"set_fsm_id({fsm_id})"
        )

    def set_balance_mode(self, balance_mode: int):
        """밸런스 모드 설정"""
        return self._execute_command(
            lambda: self.cpp_bridge.set_balance_mode(balance_mode),
            f"set_balance_mode({balance_mode})"
        )

    def set_speed_mode(self, speed_mode: int):
        """속도 모드 설정"""
        return self._execute_command(
            lambda: self.cpp_bridge.set_speed_mode(speed_mode),
            f"set_speed_mode({speed_mode})"
        )

    def continuous_gait(self, flag: bool):
        """연속 보행 설정"""
        return self._execute_command(
            lambda: self.cpp_bridge.continuous_gait(flag),
            f"continuous_gait({flag})"
        )

    def switch_move_mode(self, flag: bool):
        """이동 모드 전환"""
        return self._execute_command(
            lambda: self.cpp_bridge.switch_move_mode(flag),
            f"switch_move_mode({flag})"
        )

    # ========== 고급 제어 메소드들 ==========
    def set_velocity(self, vx: float, vy: float, omega: float, duration: float = 1.0):
        """속도 설정"""
        return self._execute_command(
            lambda: self.cpp_bridge.set_velocity(vx, vy, omega, duration),
            f"set_velocity(vx={vx}, vy={vy}, omega={omega}, duration={duration})"
        )

    def set_swing_height(self, height: float):
        """스윙 높이 설정"""
        return self._execute_command(
            lambda: self.cpp_bridge.set_swing_height(height),
            f"set_swing_height({height})"
        )

    def set_stand_height(self, height: float):
        """서기 높이 설정"""
        return self._execute_command(
            lambda: self.cpp_bridge.set_stand_height(height),
            f"set_stand_height({height})"
        )

    def set_task_id(self, task_id: int):
        """태스크 ID 설정"""
        return self._execute_command(
            lambda: self.cpp_bridge.set_task_id(task_id),
            f"set_task_id({task_id})"
        )

    # ========== 상태 조회 메소드들 ==========
    def get_status(self):
        """상태 조회"""
        with self._lock:
            return self.status

    def get_fsm_id(self):
        """FSM ID 조회"""
        try:
            if self.cpp_bridge:
                return self.cpp_bridge.get_fsm_id()
            else:
                return -1, 0
        except Exception as e:
            print(f"[ERROR] Get FSM ID failed: {e}")
            return -1, 0

    def get_balance_mode(self):
        """밸런스 모드 조회"""
        try:
            if self.cpp_bridge:
                return self.cpp_bridge.get_balance_mode()
            else:
                return -1, 0
        except Exception as e:
            print(f"[ERROR] Get balance mode failed: {e}")
            return -1, 0

    def get_swing_height(self):
        """스윙 높이 조회"""
        try:
            if self.cpp_bridge:
                return self.cpp_bridge.get_swing_height()
            else:
                return -1, 0.0
        except Exception as e:
            print(f"[ERROR] Get swing height failed: {e}")
            return -1, 0.0

    def get_stand_height(self):
        """서기 높이 조회"""
        try:
            if self.cpp_bridge:
                return self.cpp_bridge.get_stand_height()
            else:
                return -1, 0.0
        except Exception as e:
            print(f"[ERROR] Get stand height failed: {e}")
            return -1, 0.0

    def disconnect(self):
        """연결 해제"""
        try:
            if self.cpp_bridge:
                self.cpp_bridge.disconnect()
                self.cpp_bridge = None
            print("[SUCCESS] G1SubController disconnected")
        except Exception as e:
            print(f"[WARNING] Disconnect error: {e}")