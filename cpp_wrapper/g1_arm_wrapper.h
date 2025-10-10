#ifndef G1_ARM_WRAPPER_H
#define G1_ARM_WRAPPER_H

#ifdef __cplusplus
extern "C" {
#endif

// 구조체 정의
typedef struct {
    int code;
    char* data;
} StringResult;

// 클래스 포인터 타입 (opaque pointer)
typedef void* ArmClientHandle;

// 초기화/해제 함수
ArmClientHandle create_arm_client(const char* network_interface);
void destroy_arm_client(ArmClientHandle handle);
int init_arm_client(ArmClientHandle handle);
int set_arm_timeout(ArmClientHandle handle, float timeout);

// API 함수들
int execute_action(ArmClientHandle handle, int action_id);
StringResult get_action_list(ArmClientHandle handle);

// 메모리 해제 함수
void free_string_result(StringResult result);

#ifdef __cplusplus
}
#endif

#endif // G1_ARM_WRAPPER_H