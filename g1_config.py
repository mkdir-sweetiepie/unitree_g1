### ROBOT
# Defines robot identity, type and classification

ROBOT_INFO = {
    "id": "unitree_g1",
    "model": "unitree_g1",
    "category": "sample",
    "api_key": "4adb982ba0d6a7c4b9b8d7f70d71d440"
}

# Camera settings: device index and resolution
VIDEO_INFO = {
    "front_cam": {"source": 0, "width": 1920, "height": 1080},
    # "rear": {"source": 2, "width": 1280, "height": 720},
}

# Audio I/O devices
AUDIO_INFO = {
    #"audio": {"input": "NM-CSP01", "output": "NM-CSP01"},
    "audio": {"input": "default", "output": "default"},
}

### OPERATOR
# Operator account credentials for system login

# OPERATOR_INFO = {
#     'id': "oyster",
#     'password': '@Akrenddl3',
# }