#ifndef G1_LOCO_WRAPPER_H
#define G1_LOCO_WRAPPER_H

#ifdef __cplusplus
extern "C" {
#endif

// 구조체 정의
typedef struct {
    int code;
    int value;
} IntResult;

typedef struct {
    int code;
    float value;
} FloatResult;

// 클래스 포인터 타입 (opaque pointer)
typedef void* LocoClientHandle;

// 초기화/해제 함수
LocoClientHandle create_loco_client(const char* network_interface);
void destroy_loco_client(LocoClientHandle handle);
int init_loco_client(LocoClientHandle handle);
int set_timeout(LocoClientHandle handle, float timeout);

// GET 함수들
IntResult get_fsm_id(LocoClientHandle handle);
IntResult get_fsm_mode(LocoClientHandle handle);
IntResult get_balance_mode(LocoClientHandle handle);
FloatResult get_swing_height(LocoClientHandle handle);
FloatResult get_stand_height(LocoClientHandle handle);

// SET 함수들
int set_fsm_id(LocoClientHandle handle, int fsm_id);
int set_balance_mode(LocoClientHandle handle, int balance_mode);
int set_swing_height(LocoClientHandle handle, float swing_height);
int set_stand_height(LocoClientHandle handle, float stand_height);
int set_velocity(LocoClientHandle handle, float vx, float vy, float omega, float duration);
int set_task_id(LocoClientHandle handle, int task_id);
int set_speed_mode(LocoClientHandle handle, int speed_mode);

// 고수준 동작 함수들
int damp(LocoClientHandle handle);
int start_robot(LocoClientHandle handle);
int stand_up(LocoClientHandle handle);
int squat(LocoClientHandle handle);
int sit(LocoClientHandle handle);
int zero_torque(LocoClientHandle handle);
int stop_move(LocoClientHandle handle);
int high_stand(LocoClientHandle handle);
int low_stand(LocoClientHandle handle);
int balance_stand(LocoClientHandle handle);
int continuous_gait(LocoClientHandle handle, int flag);
int switch_move_mode(LocoClientHandle handle, int flag);
int move_robot(LocoClientHandle handle, float vx, float vy, float vyaw);
int wave_hand(LocoClientHandle handle, int turn_flag);
int shake_hand(LocoClientHandle handle, int stage);

#ifdef __cplusplus
}
#endif

#endif // G1_LOCO_WRAPPER_H