from pubsub import pub
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(sys.executable), "../..")))

from gerri.robot.examples.unitree_g1.g1_sub_controller import G1SubController
from gerri.robot.status_manager import StatusManager


class G1BaseController:
    def __init__(self, robot_info, sub_controller=None, **params):
        self.robot_info = robot_info
        self.robot_id = robot_info['id']
        self.robot_category = robot_info['category']
        self.robot_model = robot_info['model']

        self.sub_controller: G1SubController = sub_controller
        if self.sub_controller:
            self.sub_controller.base_controller = self
        pub.subscribe(self.receive_message, "receive_message")

        # 키 매핑 테이블 - 필수 기능 우선 배치
        self.joy_mapping = {
            # ========== 기본 이동 (axes) - 필수 ==========
            ('axes', 1, 1): ('Move Backward #s', lambda: self.sub_controller.move_backward()),
            ('axes', 1, -1): ('Move Forward #w', lambda: self.sub_controller.move_forward()),
            ('axes', 0, 1): ('Move Right #d', lambda: self.sub_controller.move_right()),
            ('axes', 0, -1): ('Move Left #a', lambda: self.sub_controller.move_left()),
            
            # ========== 회전 및 정지 (buttons) - 필수 ==========
            ('buttons', 1, 1): ('Turn Right #e', lambda: self.sub_controller.turn_right()),
            ('buttons', 2, 1): ('Turn Left #q', lambda: self.sub_controller.turn_left()),
            ('buttons', 3, 1): ('Stop Motion #r', lambda: self.sub_controller.stop()),
            
            # ========== 자세 제어 (buttons) - 필수 ==========
            ('buttons', 4, 1): ('Sit Down #z', lambda: self.sub_controller.sit_down()),
            ('buttons', 5, 1): ('Stand Up #c', lambda: self.sub_controller.stand_up()),
            ('buttons', 0, 1): ('Enable Motion #space', lambda: self.sub_controller.enable_motion()),
            
            # ========== FSM 제어 (buttons) - 중요 ==========
            ('buttons', 6, 1): ('Set FSM ID 1 #1', lambda: self.sub_controller.set_fsm_id(1)),
            ('buttons', 7, 1): ('Set FSM ID 4 #3', lambda: self.sub_controller.set_fsm_id(4)),
            
            # ========== 모드 제어 (buttons) - 중요 ==========
            ('buttons', 8, 1): ('Set FSM ID 500 #6', lambda: self.sub_controller.set_fsm_id(500)),
            ('buttons', 9, 1): ('Set FSM ID 801 #7', lambda: self.sub_controller.set_fsm_id(801)),
            
            # ========== 손 제어 (buttons) - 중요 ==========
            ('buttons', 10, 1): ('Wave Hand #h', lambda: self.sub_controller.wave_hand()),
            ('buttons', 11, 1): ('Shake Hand #j', lambda: self.sub_controller.shake_hand()),

            # ========== 안전 제어 (buttons) - 중요 ==========
            ('buttons', 12, 1): ('Damp Mode', lambda: self.sub_controller.damp()),
            ('buttons', 13, 1): ('Zero Torque', lambda: self.sub_controller.zero_torque()),
            
            # ========== 고급 자세 (buttons) - 유용 ==========
            ('buttons', 14, 1): ('Squat', lambda: self.sub_controller.squat()),
            ('buttons', 15, 1): ('Balance Stand', lambda: self.sub_controller.balance_stand()),
            
            # ========== 추가 제어 (axes 활용) - 고급 ==========
            ('axes', 2, 1): ('Switch Move Mode ON', lambda: self.sub_controller.switch_move_mode(True)),
            ('axes', 2, -1): ('Switch Move Mode OFF', lambda: self.sub_controller.switch_move_mode(False)),
            ('axes', 3, 1): ('High Stand', lambda: self.sub_controller.high_stand()),
            ('axes', 3, -1): ('Low Stand', lambda: self.sub_controller.low_stand()),
        }

        print(f"[INFO] G1BaseController initialized with {len(self.joy_mapping)} key mappings")

    def receive_message(self, message):
        if 'topic' in message:
            topic = message['topic']
            value = message['value']

            try:
                if topic == '/joy':
                    self._handle_joy_input(value)
                else:
                    self.send_message({'topic': 'callback_' + topic, 'value': 'callback_' + value, 'target': 'all'})
            except AttributeError as e:
                print(f"[ERROR] Controller does not support topic '{topic}': {e}")
            except Exception as e:
                print(f"[ERROR] Error processing topic '{topic}': {e}")
        
        pub.sendMessage('send_message', message=message)

    def _handle_joy_input(self, joy_data):
        """Joy 입력 처리 - 딕셔너리 매핑 사용"""
        command_executed = False
        
        try:
            # 모든 매핑을 확인
            for (input_type, index, expected_value), (description, action) in self.joy_mapping.items():
                try:
                    if input_type == 'axes':
                        if len(joy_data.get('axes', [])) > index and joy_data['axes'][index] == expected_value:
                            print(f"[CONTROL] {description}")
                            result = action()
                            if result != 0 and result != -1:
                                print(f"[INFO] Command result: {result}")
                            command_executed = True
                            break
                    elif input_type == 'buttons':
                        if len(joy_data.get('buttons', [])) > index and joy_data['buttons'][index] == expected_value:
                            print(f"[CONTROL] {description}")
                            result = action()
                            if result != 0 and result != -1:
                                print(f"[INFO] Command result: {result}")
                            command_executed = True
                            break
                except (IndexError, KeyError, TypeError) as e:
                    print(f"[WARNING] Error accessing joy input {input_type}[{index}]: {e}")
                    continue
            
            # 아무 명령도 실행되지 않았으면 정지
            if not command_executed:
                print('[CONTROL] No mapping found - stopping robot')
                self.sub_controller.set_velocity(0, 0, 0, 0)
                
        except Exception as e:
            print(f"[ERROR] Joy input processing failed: {e}")
            # 안전을 위해 정지
            try:
                self.sub_controller.stop()
            except:
                pass

    def send_message(self, message):
        """메시지 전송"""
        pub.sendMessage('send_message', message=message)

    def connect(self):
        """연결 설정"""
        if self.sub_controller:
            self.sub_controller.connect()
            
            # StatusManager 초기화 (gerri 시스템 연동)
            try:
                self.status_manager = StatusManager(self.robot_info, self.sub_controller)
                print("[SUCCESS] StatusManager initialized")
            except Exception as e:
                print(f"[WARNING] StatusManager initialization failed: {e}")
                print("[INFO] Continuing without StatusManager")
            
            print("[SUCCESS] G1BaseController connected")
        else:
            print("[ERROR] No sub_controller available for connection")

    def disconnect(self):
        """연결 해제"""
        if self.sub_controller:
            self.sub_controller.disconnect()
            print("[SUCCESS] G1BaseController disconnected")

    def get_robot_status(self):
        """로봇 상태 조회"""
        if self.sub_controller:
            return self.sub_controller.get_status()
        return None

    def get_fsm_status(self):
        """FSM 상태 조회"""
        if self.sub_controller:
            code, fsm_id = self.sub_controller.get_fsm_id()
            return {"code": code, "fsm_id": fsm_id}
        return {"code": -1, "fsm_id": 0}

    def emergency_stop(self):
        """긴급 정지"""
        if self.sub_controller:
            return self.sub_controller.stop()
        return -1

    def print_key_mappings(self):
        """키 매핑 정보 출력 (디버깅용)"""
        print("\n[INFO] Available Key Mappings:")
        print("=" * 50)
        for (input_type, index, value), (description, _) in self.joy_mapping.items():
            print(f"  {input_type}[{index}] = {value} → {description}")
        print("=" * 50)
        print(f"Total mappings: {len(self.joy_mapping)}\n")
