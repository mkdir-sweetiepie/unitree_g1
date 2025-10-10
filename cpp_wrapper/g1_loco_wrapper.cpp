#include "g1_loco_wrapper.h"
#include <unitree/robot/g1/loco/g1_loco_api.hpp>
#include <unitree/robot/g1/loco/g1_loco_client.hpp>
#include <iostream>
#include <memory>
#include <cstring>
#include <cstdlib>

// 올바른 네임스페이스 사용

// Internal wrapper class - 예제와 동일한 방식 사용
class G1LocoClientWrapper {
public:
    unitree::robot::g1::LocoClient client;
    bool continous_move_ = false;

    G1LocoClientWrapper() {
        // Constructor
    }

    ~G1LocoClientWrapper() {
        // Destructor
    }
};

// C interface implementations
extern "C" {

LocoClientHandle create_loco_client(const char* network_interface) {
    try {
        std::cout << "Initializing ChannelFactory with interface: " << network_interface << std::endl;

        // Initialize channel factory - 예제와 동일한 방식
        unitree::robot::ChannelFactory::Instance()->Init(0, network_interface);
        std::cout << "ChannelFactory initialized successfully" << std::endl;

        // Create wrapper
        G1LocoClientWrapper* wrapper = new G1LocoClientWrapper();
        std::cout << "LocoClient wrapper created successfully" << std::endl;
        return static_cast<LocoClientHandle>(wrapper);
    } catch (const std::exception& e) {
        std::cerr << "Error creating loco client: " << e.what() << std::endl;
        return nullptr;
    }
}

void destroy_loco_client(LocoClientHandle handle) {
    if (handle) {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        delete wrapper;
    }
}

int init_loco_client(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        wrapper->client.Init();
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error initializing client: " << e.what() << std::endl;
        return -1;
    }
}

int set_timeout(LocoClientHandle handle, float timeout) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        wrapper->client.SetTimeout(timeout);
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error setting timeout: " << e.what() << std::endl;
        return -1;
    }
}

// GET 함수들
IntResult get_fsm_id(LocoClientHandle handle) {
    IntResult result = {-1, 0};
    if (!handle) return result;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        int fsm_id = 0;
        wrapper->client.GetFsmId(fsm_id);  // return code 무시 (SDK 예제와 동일)
        result.code = 0;  // 항상 성공으로 처리
        result.value = fsm_id;
    } catch (const std::exception& e) {
        std::cerr << "Error getting FSM ID: " << e.what() << std::endl;
        result.code = -1;
    }
    return result;
}

IntResult get_fsm_mode(LocoClientHandle handle) {
    IntResult result = {-1, 0};
    if (!handle) return result;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        int fsm_mode = 0;
        wrapper->client.GetFsmMode(fsm_mode);  // return code 무시 (SDK 예제와 동일)
        result.code = 0;  // 항상 성공으로 처리
        result.value = fsm_mode;
    } catch (const std::exception& e) {
        std::cerr << "Error getting FSM mode: " << e.what() << std::endl;
        result.code = -1;
    }
    return result;
}

IntResult get_balance_mode(LocoClientHandle handle) {
    IntResult result = {-1, 0};
    if (!handle) return result;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        int balance_mode = 0;
        wrapper->client.GetBalanceMode(balance_mode);  // return code 무시 (SDK 예제와 동일)
        result.code = 0;  // 항상 성공으로 처리
        result.value = balance_mode;
    } catch (const std::exception& e) {
        std::cerr << "Error getting balance mode: " << e.what() << std::endl;
        result.code = -1;
    }
    return result;
}

FloatResult get_swing_height(LocoClientHandle handle) {
    FloatResult result = {-1, 0.0f};
    if (!handle) return result;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        float swing_height = 0.0f;
        wrapper->client.GetSwingHeight(swing_height);  // return code 무시 (SDK 예제와 동일)
        result.code = 0;  // 항상 성공으로 처리
        result.value = swing_height;
    } catch (const std::exception& e) {
        std::cerr << "Error getting swing height: " << e.what() << std::endl;
        result.code = -1;
    }
    return result;
}

FloatResult get_stand_height(LocoClientHandle handle) {
    FloatResult result = {-1, 0.0f};
    if (!handle) return result;

    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        float stand_height = 0.0f;
        wrapper->client.GetStandHeight(stand_height);  // return code 무시 (SDK 예제와 동일)
        result.code = 0;  // 항상 성공으로 처리
        result.value = stand_height;
    } catch (const std::exception& e) {
        std::cerr << "Error getting stand height: " << e.what() << std::endl;
        result.code = -1;
    }
    return result;
}

// SET 함수들
int set_fsm_id(LocoClientHandle handle, int fsm_id) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.SetFsmId(fsm_id);
    } catch (const std::exception& e) {
        std::cerr << "Error setting FSM ID: " << e.what() << std::endl;
        return -1;
    }
}

int set_balance_mode(LocoClientHandle handle, int balance_mode) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.SetBalanceMode(balance_mode);
    } catch (const std::exception& e) {
        std::cerr << "Error setting balance mode: " << e.what() << std::endl;
        return -1;
    }
}

int set_swing_height(LocoClientHandle handle, float swing_height) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.SetSwingHeight(swing_height);
    } catch (const std::exception& e) {
        std::cerr << "Error setting swing height: " << e.what() << std::endl;
        return -1;
    }
}

int set_stand_height(LocoClientHandle handle, float stand_height) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.SetStandHeight(stand_height);
    } catch (const std::exception& e) {
        std::cerr << "Error setting stand height: " << e.what() << std::endl;
        return -1;
    }
}

int set_velocity(LocoClientHandle handle, float vx, float vy, float omega, float duration) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.SetVelocity(vx, vy, omega, duration);
    } catch (const std::exception& e) {
        std::cerr << "Error setting velocity: " << e.what() << std::endl;
        return -1;
    }
}

int set_task_id(LocoClientHandle handle, int task_id) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.SetTaskId(task_id);
    } catch (const std::exception& e) {
        std::cerr << "Error setting task ID: " << e.what() << std::endl;
        return -1;
    }
}

int set_speed_mode(LocoClientHandle handle, int speed_mode) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.SetSpeedMode(speed_mode);
    } catch (const std::exception& e) {
        std::cerr << "Error setting speed mode: " << e.what() << std::endl;
        return -1;
    }
}

// 고수준 동작 함수들
int damp(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.Damp();
    } catch (const std::exception& e) {
        std::cerr << "Error executing damp: " << e.what() << std::endl;
        return -1;
    }
}

int start_robot(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.Start();
    } catch (const std::exception& e) {
        std::cerr << "Error starting robot: " << e.what() << std::endl;
        return -1;
    }
}

int stand_up(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.StandUp();
    } catch (const std::exception& e) {
        std::cerr << "Error standing up: " << e.what() << std::endl;
        return -1;
    }
}

int squat(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.Squat();
    } catch (const std::exception& e) {
        std::cerr << "Error squatting: " << e.what() << std::endl;
        return -1;
    }
}

int sit(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.Sit();
    } catch (const std::exception& e) {
        std::cerr << "Error sitting: " << e.what() << std::endl;
        return -1;
    }
}

int zero_torque(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.ZeroTorque();
    } catch (const std::exception& e) {
        std::cerr << "Error setting zero torque: " << e.what() << std::endl;
        return -1;
    }
}

int stop_move(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.StopMove();
    } catch (const std::exception& e) {
        std::cerr << "Error stopping movement: " << e.what() << std::endl;
        return -1;
    }
}

int high_stand(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.HighStand();
    } catch (const std::exception& e) {
        std::cerr << "Error high standing: " << e.what() << std::endl;
        return -1;
    }
}

int low_stand(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.LowStand();
    } catch (const std::exception& e) {
        std::cerr << "Error low standing: " << e.what() << std::endl;
        return -1;
    }
}

int balance_stand(LocoClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.BalanceStand();
    } catch (const std::exception& e) {
        std::cerr << "Error balance standing: " << e.what() << std::endl;
        return -1;
    }
}

int continuous_gait(LocoClientHandle handle, int flag) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.ContinuousGait(flag != 0);
    } catch (const std::exception& e) {
        std::cerr << "Error setting continuous gait: " << e.what() << std::endl;
        return -1;
    }
}

int switch_move_mode(LocoClientHandle handle, int flag) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        wrapper->continous_move_ = (flag != 0);
        return wrapper->client.SwitchMoveMode(flag != 0);
    } catch (const std::exception& e) {
        std::cerr << "Error switching move mode: " << e.what() << std::endl;
        return -1;
    }
}

int move_robot(LocoClientHandle handle, float vx, float vy, float vyaw) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.Move(vx, vy, vyaw, wrapper->continous_move_);
    } catch (const std::exception& e) {
        std::cerr << "Error moving robot: " << e.what() << std::endl;
        return -1;
    }
}

int wave_hand(LocoClientHandle handle, int turn_flag) {
    if (!handle) return -1;
    
    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.WaveHand(turn_flag != 0);
    } catch (const std::exception& e) {
        std::cerr << "Error waving hand: " << e.what() << std::endl;
        return -1;
    }
}

int shake_hand(LocoClientHandle handle, int stage) {
    if (!handle) return -1;

    try {
        G1LocoClientWrapper* wrapper = static_cast<G1LocoClientWrapper*>(handle);
        return wrapper->client.ShakeHand(stage);
    } catch (const std::exception& e) {
        std::cerr << "Error shaking hand: " << e.what() << std::endl;
        return -1;
    }
}

} // extern "C"