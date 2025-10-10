#include "g1_arm_wrapper.h"
#include <unitree/robot/g1/arm/g1_arm_action_api.hpp>
#include <unitree/robot/g1/arm/g1_arm_action_client.hpp>
#include <iostream>
#include <memory>
#include <cstring>
#include <cstdlib>

// Internal wrapper class
class G1ArmClientWrapper {
public:
    unitree::robot::g1::G1ArmActionClient client;

    G1ArmClientWrapper() {
        // Constructor
    }

    ~G1ArmClientWrapper() {
        // Destructor
    }
};

// C interface implementations
extern "C" {

ArmClientHandle create_arm_client(const char* network_interface) {
    try {
        // ChannelFactory는 싱글톤이므로 이미 초기화되었다면 스킵
        // (loco wrapper에서 이미 초기화했을 가능성 있음)
        std::cout << "Creating ArmActionClient (ChannelFactory should be already initialized)" << std::endl;

        // Create wrapper (ChannelFactory 초기화 안 함)
        G1ArmClientWrapper* wrapper = new G1ArmClientWrapper();
        std::cout << "ArmActionClient wrapper created successfully" << std::endl;
        return static_cast<ArmClientHandle>(wrapper);
    } catch (const std::exception& e) {
        std::cerr << "Error creating arm client: " << e.what() << std::endl;
        return nullptr;
    }
}

void destroy_arm_client(ArmClientHandle handle) {
    if (handle) {
        G1ArmClientWrapper* wrapper = static_cast<G1ArmClientWrapper*>(handle);
        delete wrapper;
    }
}

int init_arm_client(ArmClientHandle handle) {
    if (!handle) return -1;
    
    try {
        G1ArmClientWrapper* wrapper = static_cast<G1ArmClientWrapper*>(handle);
        wrapper->client.Init();
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error initializing arm client: " << e.what() << std::endl;
        return -1;
    }
}

int set_arm_timeout(ArmClientHandle handle, float timeout) {
    if (!handle) return -1;
    
    try {
        G1ArmClientWrapper* wrapper = static_cast<G1ArmClientWrapper*>(handle);
        wrapper->client.SetTimeout(timeout);
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error setting timeout: " << e.what() << std::endl;
        return -1;
    }
}

int execute_action(ArmClientHandle handle, int action_id) {
    if (!handle) return -1;
    
    try {
        G1ArmClientWrapper* wrapper = static_cast<G1ArmClientWrapper*>(handle);
        int32_t ret = wrapper->client.ExecuteAction(action_id);
        return ret;
    } catch (const std::exception& e) {
        std::cerr << "Error executing action: " << e.what() << std::endl;
        return -1;
    }
}

StringResult get_action_list(ArmClientHandle handle) {
    StringResult result = {-1, nullptr};
    if (!handle) return result;
    
    try {
        G1ArmClientWrapper* wrapper = static_cast<G1ArmClientWrapper*>(handle);
        std::string data;
        int32_t ret = wrapper->client.GetActionList(data);
        
        result.code = ret;
        if (ret == 0 && !data.empty()) {
            // C 문자열로 복사
            result.data = static_cast<char*>(malloc(data.size() + 1));
            if (result.data) {
                strcpy(result.data, data.c_str());
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "Error getting action list: " << e.what() << std::endl;
        result.code = -1;
    }
    
    return result;
}

void free_string_result(StringResult result) {
    if (result.data) {
        free(result.data);
    }
}

} // extern "C"