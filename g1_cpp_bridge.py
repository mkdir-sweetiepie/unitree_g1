#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import ctypes
from ctypes import Structure, POINTER, c_void_p, c_int, c_float, c_char_p
import threading
from typing import List, Tuple, Optional

# 구조체 정의 (C++ 헤더와 동일)
class IntResult(Structure):
    _fields_ = [("code", c_int), ("value", c_int)]

class FloatResult(Structure):
    _fields_ = [("code", c_int), ("value", c_float)]

class G1CppBridge:
    """G1 LocoClient C++ Wrapper Bridge for Python"""
    
    def __init__(self, network_interface: str = "eth0"):
        self.network_interface = network_interface
        self.handle = None
        self.lib = None
        self._lock = threading.Lock()
        self._load_library()
    
    def _load_library(self):
        """C++ 공유 라이브러리 로드"""
        try:
            # 라이브러리 경로 찾기
            current_dir = os.path.dirname(os.path.abspath(__file__))
            lib_paths = [
                os.path.join(current_dir, "libg1_loco_wrapper.so"),
                os.path.join(current_dir, "cpp_wrapper", "libg1_loco_wrapper.so"),
                "./libg1_loco_wrapper.so"
            ]

            for lib_path in lib_paths:
                if os.path.exists(lib_path):
                    try:
                        print(f"[INFO] Loading C++ library: {lib_path}")
                        self.lib = ctypes.CDLL(lib_path)
                        print(f"[SUCCESS] Loaded C++ library: {lib_path}")
                        break
                    except OSError as e:
                        print(f"[ERROR] Failed to load {lib_path}: {e}")
                        continue

            if not self.lib:
                raise RuntimeError(f"Could not find or load libg1_loco_wrapper.so in paths: {lib_paths}")

            self._setup_function_signatures()

        except Exception as e:
            print(f"[ERROR] Library loading failed: {e}")
            raise
    
    def _setup_function_signatures(self):
        """함수 시그니처 설정"""
        
        # 초기화/해제 함수들
        self.lib.create_loco_client.argtypes = [c_char_p]
        self.lib.create_loco_client.restype = c_void_p
        
        self.lib.destroy_loco_client.argtypes = [c_void_p]
        self.lib.destroy_loco_client.restype = None
        
        self.lib.init_loco_client.argtypes = [c_void_p]
        self.lib.init_loco_client.restype = c_int
        
        self.lib.set_timeout.argtypes = [c_void_p, c_float]
        self.lib.set_timeout.restype = c_int
        
        # GET 함수들
        self.lib.get_fsm_id.argtypes = [c_void_p]
        self.lib.get_fsm_id.restype = IntResult
        
        self.lib.get_fsm_mode.argtypes = [c_void_p]
        self.lib.get_fsm_mode.restype = IntResult
        
        self.lib.get_balance_mode.argtypes = [c_void_p]
        self.lib.get_balance_mode.restype = IntResult
        
        self.lib.get_swing_height.argtypes = [c_void_p]
        self.lib.get_swing_height.restype = FloatResult
        
        self.lib.get_stand_height.argtypes = [c_void_p]
        self.lib.get_stand_height.restype = FloatResult
        
        # SET 함수들
        self.lib.set_fsm_id.argtypes = [c_void_p, c_int]
        self.lib.set_fsm_id.restype = c_int
        
        self.lib.set_balance_mode.argtypes = [c_void_p, c_int]
        self.lib.set_balance_mode.restype = c_int
        
        self.lib.set_swing_height.argtypes = [c_void_p, c_float]
        self.lib.set_swing_height.restype = c_int
        
        self.lib.set_stand_height.argtypes = [c_void_p, c_float]
        self.lib.set_stand_height.restype = c_int
        
        self.lib.set_velocity.argtypes = [c_void_p, c_float, c_float, c_float, c_float]
        self.lib.set_velocity.restype = c_int
        
        self.lib.set_task_id.argtypes = [c_void_p, c_int]
        self.lib.set_task_id.restype = c_int
        
        self.lib.set_speed_mode.argtypes = [c_void_p, c_int]
        self.lib.set_speed_mode.restype = c_int
        
        # 고수준 동작 함수들
        action_functions = [
            'damp', 'start_robot', 'stand_up', 'squat', 'sit', 'zero_torque',
            'stop_move', 'high_stand', 'low_stand', 'balance_stand'
        ]
        
        for func_name in action_functions:
            func = getattr(self.lib, func_name)
            func.argtypes = [c_void_p]
            func.restype = c_int
        
        # 플래그가 있는 함수들
        self.lib.continuous_gait.argtypes = [c_void_p, c_int]
        self.lib.continuous_gait.restype = c_int
        
        self.lib.switch_move_mode.argtypes = [c_void_p, c_int]
        self.lib.switch_move_mode.restype = c_int
        
        self.lib.wave_hand.argtypes = [c_void_p, c_int]
        self.lib.wave_hand.restype = c_int
        
        self.lib.shake_hand.argtypes = [c_void_p, c_int]
        self.lib.shake_hand.restype = c_int
        
        # 이동 함수
        self.lib.move_robot.argtypes = [c_void_p, c_float, c_float, c_float]
        self.lib.move_robot.restype = c_int
    
    def connect(self):
        """로봇에 연결"""
        with self._lock:
            if self.handle:
                print("[WARNING] Already connected")
                return True

            try:
                print(f"[INFO] Connecting to G1 robot via {self.network_interface}")
                interface_bytes = self.network_interface.encode('utf-8')

                self.handle = self.lib.create_loco_client(interface_bytes)
                if not self.handle:
                    raise RuntimeError("Failed to create loco client")

                result = self.lib.init_loco_client(self.handle)
                if result != 0:
                    error_msg = self._get_error_message(result)
                    raise RuntimeError(f"Client initialization failed - Code: {result}, Message: {error_msg}")

                self.lib.set_timeout(self.handle, 3.0)

                print(f"[SUCCESS] Connected to G1 robot via {self.network_interface}")
                return True

            except Exception as e:
                print(f"[ERROR] Connection failed: {e}")
                self._cleanup()
                return False

    def _cleanup(self):
        """정리"""
        try:
            if self.handle:
                self.lib.destroy_loco_client(self.handle)
                self.handle = None
        except Exception as e:
            print(f"[WARNING] Cleanup error: {e}")
    
    def disconnect(self):
        """로봇 연결 해제"""
        with self._lock:
            self._cleanup()
            print("[SUCCESS] Disconnected from G1 robot")
    
    def _check_connection(self):
        """연결 상태 확인"""
        if not self.handle:
            raise RuntimeError("Not connected to robot. Call connect() first.")
    
    def _get_error_message(self, error_code: int) -> str:
        """오류 코드를 사람이 읽을 수 있는 메시지로 변환"""
        error_messages = {
            0: "SUCCESS",
            3104: "ROBOT_NOT_READY - 로봇이 준비되지 않음 (전원, 모터 상태 확인 필요)",
            3105: "COMMUNICATION_TIMEOUT - 통신 타임아웃",
            3106: "INVALID_COMMAND - 잘못된 명령",
            3107: "ROBOT_EMERGENCY_STOP - 로봇 비상 정지 상태",
            3108: "MOTOR_ERROR - 모터 오류",
            3109: "SENSOR_ERROR - 센서 오류",
            3110: "BATTERY_LOW - 배터리 부족",
            3111: "OVERLOAD - 과부하 상태",
            3112: "CALIBRATION_REQUIRED - 캘리브레이션 필요",
            -1: "GENERAL_ERROR - 일반적인 오류"
        }
        return error_messages.get(error_code, f"UNKNOWN_ERROR_{error_code}")
    
    # ========== GET 메소드들 ==========
    def get_fsm_id(self) -> Tuple[int, int]:
        """FSM ID 조회"""
        self._check_connection()
        try:
            result = self.lib.get_fsm_id(self.handle)
            return result.code, result.value
        except Exception as e:
            print(f"[ERROR] Exception in get_fsm_id: {e}")
            raise
    
    def get_fsm_mode(self) -> Tuple[int, int]:
        """FSM 모드 조회"""
        self._check_connection()
        result = self.lib.get_fsm_mode(self.handle)
        return result.code, result.value
    
    def get_balance_mode(self) -> Tuple[int, int]:
        """밸런스 모드 조회"""
        self._check_connection()
        result = self.lib.get_balance_mode(self.handle)
        return result.code, result.value
    
    def get_swing_height(self) -> Tuple[int, float]:
        """스윙 높이 조회"""
        self._check_connection()
        result = self.lib.get_swing_height(self.handle)
        return result.code, result.value
    
    def get_stand_height(self) -> Tuple[int, float]:
        """서있는 높이 조회"""
        self._check_connection()
        result = self.lib.get_stand_height(self.handle)
        return result.code, result.value
    
    # ========== SET 메소드들 ==========
    def set_fsm_id(self, fsm_id: int) -> int:
        """FSM ID 설정"""
        self._check_connection()
        return self.lib.set_fsm_id(self.handle, fsm_id)
    
    def set_balance_mode(self, balance_mode: int) -> int:
        """밸런스 모드 설정"""
        self._check_connection()
        return self.lib.set_balance_mode(self.handle, balance_mode)
    
    def set_swing_height(self, swing_height: float) -> int:
        """스윙 높이 설정"""
        self._check_connection()
        return self.lib.set_swing_height(self.handle, swing_height)
    
    def set_stand_height(self, stand_height: float) -> int:
        """서있는 높이 설정"""
        self._check_connection()
        return self.lib.set_stand_height(self.handle, stand_height)
    
    def set_velocity(self, vx: float, vy: float, omega: float, duration: float = 1.0) -> int:
        """속도 설정"""
        self._check_connection()
        return self.lib.set_velocity(self.handle, vx, vy, omega, duration)
    
    def set_task_id(self, task_id: int) -> int:
        """태스크 ID 설정"""
        self._check_connection()
        return self.lib.set_task_id(self.handle, task_id)
    
    def set_speed_mode(self, speed_mode: int) -> int:
        """속도 모드 설정"""
        self._check_connection()
        return self.lib.set_speed_mode(self.handle, speed_mode)
    
    # ========== 고수준 동작 메소드들 ==========
    def damp(self) -> int:
        """댐핑 모드"""
        self._check_connection()
        return self.lib.damp(self.handle)
    
    def start_robot(self) -> int:
        """로봇 시작"""
        self._check_connection()
        return self.lib.start_robot(self.handle)
    
    def stand_up(self) -> int:
        """일어서기"""
        self._check_connection()
        return self.lib.stand_up(self.handle)
    
    def squat(self) -> int:
        """쪼그려 앉기"""
        self._check_connection()
        return self.lib.squat(self.handle)
    
    def sit(self) -> int:
        """앉기"""
        self._check_connection()
        return self.lib.sit(self.handle)
    
    def zero_torque(self) -> int:
        """제로 토크"""
        self._check_connection()
        return self.lib.zero_torque(self.handle)
    
    def stop_move(self) -> int:
        """이동 정지"""
        self._check_connection()
        return self.lib.stop_move(self.handle)
    
    def high_stand(self) -> int:
        """높은 자세로 서기"""
        self._check_connection()
        return self.lib.high_stand(self.handle)
    
    def low_stand(self) -> int:
        """낮은 자세로 서기"""
        self._check_connection()
        return self.lib.low_stand(self.handle)
    
    def balance_stand(self) -> int:
        """밸런스 서기"""
        self._check_connection()
        return self.lib.balance_stand(self.handle)
    
    def continuous_gait(self, flag: bool) -> int:
        """연속 보행 설정"""
        self._check_connection()
        return self.lib.continuous_gait(self.handle, 1 if flag else 0)
    
    def switch_move_mode(self, flag: bool) -> int:
        """이동 모드 전환"""
        self._check_connection()
        return self.lib.switch_move_mode(self.handle, 1 if flag else 0)
    
    def move_robot(self, vx: float, vy: float, vyaw: float) -> int:
        """로봇 이동"""
        self._check_connection()
        return self.lib.move_robot(self.handle, vx, vy, vyaw)
    
    def wave_hand(self, turn_flag: bool = False) -> int:
        """손 흔들기"""
        self._check_connection()
        return self.lib.wave_hand(self.handle, 1 if turn_flag else 0)
    
    def shake_hand(self, stage: int = -1) -> int:
        """악수 동작"""
        self._check_connection()
        return self.lib.shake_hand(self.handle, stage)
    
    def __del__(self):
        """소멸자"""
        self.disconnect()