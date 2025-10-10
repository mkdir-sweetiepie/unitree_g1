#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import ctypes
from ctypes import Structure, POINTER, c_void_p, c_int, c_float, c_char_p
import threading
from typing import Dict, Tuple, Optional

# 구조체 정의 (C++ 헤더와 동일)
class StringResult(Structure):
    _fields_ = [("code", c_int), ("data", c_char_p)]

class G1ArmBridge:
    """G1 ArmActionClient C++ Wrapper Bridge for Python"""
    
    # Action 매핑 (g1_arm_action_client.hpp와 동일)
    ACTION_MAP = {
        "release_arm": 99,
        "two_hand_kiss": 11,
        "left_kiss": 12,
        "right_kiss": 13,
        "hands_up": 15,
        "clap": 17,
        "high_five": 18,
        "hug": 19,
        "heart": 20,
        "right_heart": 21,
        "reject": 22,
        "right_hand_up": 23,
        "x_ray": 24,
        "face_wave": 25,
        "high_wave": 26,
        "shake_hand": 27,
    }
    
    # 에러 코드 매핑
    ERROR_MESSAGES = {
        -5: "ARM SDK ERROR: Arm SDK interface error",
        -6: "HOLDING ERROR: Robot is holding something",
        -7: "INVALID ACTION ID: Invalid action ID",
        -8: "INVALID FSM ID: Actions only supported in FSM ID {500, 501, 801}",
    }
    
    def __init__(self, network_interface: str = "eth0"):
        self.network_interface = network_interface
        self.handle = None
        self.lib = None
        self._lock = threading.Lock()
        self._load_library()
    
    def _load_library(self):
        """C++ 공유 라이브러리 로드"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            lib_paths = [
                os.path.join(current_dir, "libg1_arm_wrapper.so"),
                os.path.join(current_dir, "cpp_wrapper", "libg1_arm_wrapper.so"),
                "./libg1_arm_wrapper.so"
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
                raise RuntimeError(f"Could not find libg1_arm_wrapper.so in any of these paths: {lib_paths}")

            self._setup_function_signatures()
            print("[SUCCESS] Function signatures configured")

        except Exception as e:
            raise RuntimeError(f"Failed to load library: {e}")
    
    def _setup_function_signatures(self):
        """함수 시그니처 설정"""
        # create_arm_client
        self.lib.create_arm_client.argtypes = [c_char_p]
        self.lib.create_arm_client.restype = c_void_p
        
        # destroy_arm_client
        self.lib.destroy_arm_client.argtypes = [c_void_p]
        self.lib.destroy_arm_client.restype = None
        
        # init_arm_client
        self.lib.init_arm_client.argtypes = [c_void_p]
        self.lib.init_arm_client.restype = c_int
        
        # set_arm_timeout
        self.lib.set_arm_timeout.argtypes = [c_void_p, c_float]
        self.lib.set_arm_timeout.restype = c_int
        
        # execute_action
        self.lib.execute_action.argtypes = [c_void_p, c_int]
        self.lib.execute_action.restype = c_int
        
        # get_action_list
        self.lib.get_action_list.argtypes = [c_void_p]
        self.lib.get_action_list.restype = StringResult
        
        # free_string_result
        self.lib.free_string_result.argtypes = [StringResult]
        self.lib.free_string_result.restype = None
    
    def _get_error_message(self, code: int) -> str:
        """에러 코드를 메시지로 변환"""
        return self.ERROR_MESSAGES.get(code, f"Unknown error (code: {code})")
    
    def connect(self) -> bool:
        """로봇에 연결"""
        with self._lock:
            try:
                if self.handle:
                    print("[WARNING] Already connected")
                    return True

                print(f"[INFO] Connecting to G1 robot via {self.network_interface}...")
                
                interface_bytes = self.network_interface.encode('utf-8')

                print("[DEBUG] Creating arm client...")
                self.handle = self.lib.create_arm_client(interface_bytes)
                if not self.handle:
                    raise RuntimeError("Failed to create arm client")
                print(f"[DEBUG] Arm client created successfully: {self.handle}")

                print("[DEBUG] Initializing arm client...")
                result = self.lib.init_arm_client(self.handle)
                if result != 0:
                    error_msg = self._get_error_message(result)
                    raise RuntimeError(f"Client initialization failed - Code: {result}, Message: {error_msg}")
                print("[DEBUG] Arm client initialized successfully")

                print("[DEBUG] Setting timeout...")
                timeout_result = self.lib.set_arm_timeout(self.handle, 10.0)
                print(f"[DEBUG] Timeout set result: {timeout_result}")
                
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
                self.lib.destroy_arm_client(self.handle)
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
    
    # ===== ARM ACTION API =====
    
    def execute_action(self, action_id: int) -> Tuple[bool, str]:
        """
        특정 arm action 실행
        
        Args:
            action_id: 실행할 action의 ID
        
        Returns:
            (성공 여부, 메시지)
        """
        self._check_connection()
        
        with self._lock:
            try:
                result = self.lib.execute_action(self.handle, action_id)
                
                if result == 0:
                    return True, f"Action {action_id} executed successfully"
                else:
                    error_msg = self._get_error_message(result)
                    return False, f"Failed to execute action {action_id}: {error_msg}"
                    
            except Exception as e:
                return False, f"Exception during execute_action: {e}"
    
    def execute_action_by_name(self, action_name: str) -> Tuple[bool, str]:
        """
        이름으로 arm action 실행
        
        Args:
            action_name: 실행할 action의 이름 (예: "wave_hand", "clap")
        
        Returns:
            (성공 여부, 메시지)
        """
        action_id = self.ACTION_MAP.get(action_name)
        if action_id is None:
            available = ", ".join(self.ACTION_MAP.keys())
            return False, f"Unknown action '{action_name}'. Available: {available}"
        
        return self.execute_action(action_id)
    
    def get_action_list(self) -> Tuple[bool, str]:
        """
        사용 가능한 action 목록 가져오기
        
        Returns:
            (성공 여부, action 목록 JSON 문자열 or 에러 메시지)
        """
        self._check_connection()
        
        with self._lock:
            try:
                result = self.lib.get_action_list(self.handle)
                
                if result.code == 0 and result.data:
                    data = result.data.decode('utf-8')
                    self.lib.free_string_result(result)
                    return True, data
                else:
                    error_msg = self._get_error_message(result.code)
                    return False, f"Failed to get action list: {error_msg}"
                    
            except Exception as e:
                return False, f"Exception during get_action_list: {e}"
    
    def print_available_actions(self):
        """사용 가능한 action 목록 출력"""
        print("\n=== Available Actions ===")
        for name, action_id in sorted(self.ACTION_MAP.items()):
            print(f"  - {name:20s} (ID: {action_id})")
        print("========================\n")
    
    def __del__(self):
        """소멸자"""
        self.disconnect()


# ===== 사용 예제 =====
if __name__ == "__main__":
    import time
    
    # 브릿지 생성 및 연결
    bridge = G1ArmBridge(network_interface="eth0")
    
    if not bridge.connect():
        print("Failed to connect to robot")
        exit(1)
    
    # 사용 가능한 action 출력
    bridge.print_available_actions()
    
    # Action 목록 가져오기
    success, action_list = bridge.get_action_list()
    if success:
        print(f"Action list from robot: {action_list}\n")
    
    # 특정 action 실행 (이름으로)
    print("Executing 'hands_up' action...")
    success, msg = bridge.execute_action_by_name("hands_up")
    print(f"Result: {msg}")
    time.sleep(3)
    
    # 특정 action 실행 (ID로)
    print("\nExecuting action ID 17 (clap)...")
    success, msg = bridge.execute_action(17)
    print(f"Result: {msg}")
    time.sleep(3)
    
    # 여러 action 순차 실행
    actions = ["face_wave", "heart", "reject"]
    for action in actions:
        print(f"\nExecuting '{action}'...")
        success, msg = bridge.execute_action_by_name(action)
        print(f"Result: {msg}")
        time.sleep(3)
    
    # 연결 해제
    bridge.disconnect()
    print("Demo completed")