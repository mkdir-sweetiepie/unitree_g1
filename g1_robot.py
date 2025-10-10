import os, sys
import time

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(sys.executable), "../..")))

from _and_.and_robot import AdaptiveNetworkDaemon
from g1_config import ROBOT_INFO, VIDEO_INFO, AUDIO_INFO

# Initialize communication module (AND)
daemon = AdaptiveNetworkDaemon(
    robot_info=ROBOT_INFO,
    network='ketirtc',
    command="command",
    video_info=VIDEO_INFO,
    audio_info=AUDIO_INFO,
)
daemon.connect()

# Initialize robot controller (GERRI)
# - If the model in ROBOT_INFO is predefined, the base controller will auto-select it.
# - Otherwise, manually specify a sub-controller as shown below.

from gerri.robot.examples.unitree_g1.g1_base_controller import G1BaseController
from gerri.robot.examples.unitree_g1.g1_sub_controller import G1SubController

robot = G1BaseController(ROBOT_INFO, sub_controller=G1SubController())
robot.connect()

# Keep process alive
while True:
    time.sleep(1)