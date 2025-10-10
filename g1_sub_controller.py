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

# C++ Bridge 로드
try:
    print("[INFO] Loading C++ Bridges...")
    from g1_cpp_bridge import G1CppBridge
    LOCO_BRIDGE_AVAILABLE = True
    print("[SUCCESS] Loco Bridge loaded successfully")
except Exception as e:
    print(f"[ERROR] Loco Bridge failed: {e}")
    print("[ERROR] Cannot operate without Loco Bridge")
    LOCO_BRIDGE_AVAILABLE = False

try:
    from g1_arm_bridge import G1ArmBridge
    ARM_BRIDGE_AVAILABLE = True
    print("[SUCCESS] Arm Bridge loaded successfully")
except Exception as e:
    print(f"[WARNING] Arm Bridge failed: {e}")
    print("[INFO] Continuing without Arm control")
    ARM_BRIDGE_AVAILABLE = False


class G1SubController:
    def __init__(self):
        self.robot_controller = None
        self.base_controller = None
        self.status = None
        self._lock = threading.Lock()

        # Robot control clients
        self.loco_bridge = None  # 하체 제어 (이동, 자세)
        self.arm_bridge = None   # 상체 제어 (팔 동작)

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
        """로봇 클라이언트 초기화 (Loco + Arm Bridge)"""
        network_interface = "eth0"  # 실제 로봇 연결을 위한 네트워크 인터페이스

        # 1. Loco Bridge 초기화 (반드시 먼저! ChannelFactory 초기화)
        if not LOCO_BRIDGE_AVAILABLE:
            print("[ERROR] Loco Bridge not available - robot control disabled")
            return

        try:
            print("[INFO] Initializing Loco Bridge...")
            self.loco_bridge = G1CppBridge(network_interface)

            if self.loco_bridge.connect():
                print("[SUCCESS] Loco Bridge connected")

                # 기본 기능 테스트
                code, fsm_id = self.loco_bridge.get_fsm_id()
                if code == 0:
                    print(f"[SUCCESS] Loco Bridge working - FSM ID: {fsm_id}")
                else:
                    print(f"[WARNING] FSM test returned code {code}, but continuing")
            else:
                raise RuntimeError("Loco connection failed")

        except Exception as e:
            print(f"[ERROR] Loco Bridge initialization failed: {e}")
            self.loco_bridge = None
            return

        # 2. Arm Bridge 초기화 (선택사항, loco 이후에)
        if not ARM_BRIDGE_AVAILABLE:
            print("[INFO] Arm Bridge not available - continuing without arm control")
            return

        try:
            print("[INFO] Initializing Arm Bridge...")
            self.arm_bridge = G1ArmBridge(network_interface)

            if self.arm_bridge.connect():
                print("[SUCCESS] Arm Bridge connected")
            else:
                print("[WARNING] Arm connection failed, continuing without arm control")
                self.arm_bridge = None

        except Exception as e:
            print(f"[WARNING] Arm Bridge initialization failed: {e}")
            self.arm_bridge = None

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
            if self.loco_bridge:
                # Loco Bridge를 통한 실제 상태 조회
                code, fsm_id = self.loco_bridge.get_fsm_id()
                if code == 0:
                    self.status.motion_state = f"fsm_id_{fsm_id}"
                else:
                    self.status.motion_state = "unknown"
            else:
                # Loco Bridge 없음
                self.status.motion_state = "disconnected"

        except Exception as e:
            print(f"[WARNING] Failed to update status: {e}")
            self.status.motion_state = "error"

    def _execute_loco_command(self, command_func, command_name):
        """Loco 명령 실행 헬퍼 메소드"""
        try:
            with self._lock:
                if self.loco_bridge:
                    result = command_func()
                    print(f"[CONTROL] {command_name} executed - result: {result}")
                    return result
                else:
                    print(f"[ERROR] No Loco Bridge connection - {command_name} ignored")
                    return -1
        except Exception as e:
            print(f"[ERROR] {command_name} failed: {e}")
            return -1

    def _execute_arm_command(self, action_name, command_name):
        """Arm 명령 실행 헬퍼 메소드"""
        try:
            with self._lock:
                if self.arm_bridge:
                    success, msg = self.arm_bridge.execute_action_by_name(action_name)
                    print(f"[CONTROL] {command_name} - {msg}")
                    return 0 if success else -1
                else:
                    print(f"[ERROR] No Arm Bridge connection - {command_name} ignored")
                    return -1
        except Exception as e:
            print(f"[ERROR] {command_name} failed: {e}")
            return -1

    # ========== 기본 이동 제어 메소드들 ==========
    def move_forward(self):
        """전진"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.move_robot(self.default_velocity, 0, 0),
            "move_forward"
        )

    def move_backward(self):
        """후진"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.move_robot(-self.default_velocity, 0, 0),
            "move_backward"
        )

    def move_left(self):
        """좌측 이동"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.move_robot(0, self.default_velocity, 0),
            "move_left"
        )

    def move_right(self):
        """우측 이동"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.move_robot(0, -self.default_velocity, 0),
            "move_right"
        )

    def turn_left(self):
        """좌회전"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.move_robot(0, 0, self.default_angular_velocity),
            "turn_left"
        )

    def turn_right(self):
        """우회전"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.move_robot(0, 0, -self.default_angular_velocity),
            "turn_right"
        )

    def stop(self):
        """정지"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.stop_move(),
            "stop"
        )

    # ========== 자세 제어 메소드들 ==========
    def stand_up(self):
        """일어서기"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.stand_up(),
            "stand_up"
        )

    def sit_down(self):
        """앉기"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.sit(),
            "sit_down"
        )

    def enable_motion(self):
        """모션 활성화 (로봇 시작)"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.start_robot(),
            "enable_motion"
        )

    def squat(self):
        """쪼그려 앉기"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.squat(),
            "squat"
        )

    def balance_stand(self):
        """밸런스 스탠드"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.balance_stand(),
            "balance_stand"
        )

    def damp(self):
        """댐핑 모드"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.damp(),
            "damp"
        )

    def zero_torque(self):
        """제로 토크"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.zero_torque(),
            "zero_torque"
        )

    def high_stand(self):
        """높은 자세로 서기"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.high_stand(),
            "high_stand"
        )

    def low_stand(self):
        """낮은 자세로 서기"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.low_stand(),
            "low_stand"
        )

    # ========== 손 제어 메소드들 ==========
    def wave_hand(self):
        """손 흔들기"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.wave_hand(),
            "wave_hand"
        )

    def shake_hand(self, stage=-1):
        """악수 동작"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.shake_hand(stage),
            f"shake_hand(stage={stage})"
        )

    # ========== FSM 및 모드 제어 메소드들 ==========
    def set_fsm_id(self, fsm_id: int):
        """FSM ID 설정"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.set_fsm_id(fsm_id),
            f"set_fsm_id({fsm_id})"
        )

    def set_balance_mode(self, balance_mode: int):
        """밸런스 모드 설정"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.set_balance_mode(balance_mode),
            f"set_balance_mode({balance_mode})"
        )

    def set_speed_mode(self, speed_mode: int):
        """속도 모드 설정"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.set_speed_mode(speed_mode),
            f"set_speed_mode({speed_mode})"
        )

    def continuous_gait(self, flag: bool):
        """연속 보행 설정"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.continuous_gait(flag),
            f"continuous_gait({flag})"
        )

    def switch_move_mode(self, flag: bool):
        """이동 모드 전환"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.switch_move_mode(flag),
            f"switch_move_mode({flag})"
        )

    # ========== 고급 제어 메소드들 ==========
    def set_velocity(self, vx: float, vy: float, omega: float, duration: float = 1.0):
        """속도 설정"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.set_velocity(vx, vy, omega, duration),
            f"set_velocity(vx={vx}, vy={vy}, omega={omega}, duration={duration})"
        )

    def set_swing_height(self, height: float):
        """스윙 높이 설정"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.set_swing_height(height),
            f"set_swing_height({height})"
        )

    def set_stand_height(self, height: float):
        """서기 높이 설정"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.set_stand_height(height),
            f"set_stand_height({height})"
        )

    def set_task_id(self, task_id: int):
        """태스크 ID 설정"""
        return self._execute_loco_command(
            lambda: self.loco_bridge.set_task_id(task_id),
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
            if self.loco_bridge:
                return self.loco_bridge.get_fsm_id()
            else:
                return -1, 0
        except Exception as e:
            print(f"[ERROR] Get FSM ID failed: {e}")
            return -1, 0

    def get_balance_mode(self):
        """밸런스 모드 조회"""
        try:
            if self.loco_bridge:
                return self.loco_bridge.get_balance_mode()
            else:
                return -1, 0
        except Exception as e:
            print(f"[ERROR] Get balance mode failed: {e}")
            return -1, 0

    def get_swing_height(self):
        """스윙 높이 조회"""
        try:
            if self.loco_bridge:
                return self.loco_bridge.get_swing_height()
            else:
                return -1, 0.0
        except Exception as e:
            print(f"[ERROR] Get swing height failed: {e}")
            return -1, 0.0

    def get_stand_height(self):
        """서기 높이 조회"""
        try:
            if self.loco_bridge:
                return self.loco_bridge.get_stand_height()
            else:
                return -1, 0.0
        except Exception as e:
            print(f"[ERROR] Get stand height failed: {e}")
            return -1, 0.0

    def disconnect(self):
        """연결 해제"""
        try:
            if self.loco_bridge:
                self.loco_bridge.disconnect()
                self.loco_bridge = None
            print("[SUCCESS] G1SubController disconnected")
        except Exception as e:
            print(f"[WARNING] Disconnect error: {e}")
    # ========== ARM 제어 메소드들 (상체 동작) ==========
    def arm_wave(self):
        """손 높이 흔들기"""
        return self._execute_arm_command("high_wave", "arm_wave")

    def arm_clap(self):
        """박수 치기"""
        return self._execute_arm_command("clap", "arm_clap")

    def arm_heart(self):
        """하트 만들기"""
        return self._execute_arm_command("heart", "arm_heart")

    def arm_hug(self):
        """포옹 자세"""
        return self._execute_arm_command("hug", "arm_hug")

    def arm_hands_up(self):
        """손 들기"""
        return self._execute_arm_command("hands_up", "arm_hands_up")

    def arm_high_five(self):
        """하이파이브"""
        return self._execute_arm_command("high_five", "arm_high_five")

    def arm_reject(self):
        """거절 동작"""
        return self._execute_arm_command("reject", "arm_reject")

    def arm_shake_hand(self):
        """악수 (arm action)"""
        return self._execute_arm_command("shake_hand", "arm_shake_hand")

    def arm_action(self, action_name: str):
        """일반 arm action 실행"""
        return self._execute_arm_command(action_name, f"arm_action({action_name})")

    def arm_release(self):
        """팔 해제"""
        return self._execute_arm_command("release_arm", "arm_release")

    # ========== ARM 추가 액션들 (코드로만 사용 가능) ==========
    def arm_two_hand_kiss(self):
        """양손 키스"""
        return self._execute_arm_command("two_hand_kiss", "arm_two_hand_kiss")

    def arm_left_kiss(self):
        """왼손 키스"""
        return self._execute_arm_command("left_kiss", "arm_left_kiss")

    def arm_right_kiss(self):
        """오른손 키스"""
        return self._execute_arm_command("right_kiss", "arm_right_kiss")

    def arm_right_heart(self):
        """오른손 하트"""
        return self._execute_arm_command("right_heart", "arm_right_heart")

    def arm_right_hand_up(self):
        """오른손 들기"""
        return self._execute_arm_command("right_hand_up", "arm_right_hand_up")

    def arm_x_ray(self):
        """X-ray 포즈"""
        return self._execute_arm_command("x_ray", "arm_x_ray")

    def arm_face_wave(self):
        """얼굴 앞 손 흔들기"""
        return self._execute_arm_command("face_wave", "arm_face_wave")
