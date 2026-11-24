# One container: rosbridge (:9090) + turtlesim (headless, under Xvfb) + the gate.
# docker build -t ros2-voice-gate . && docker run --rm -p 9090:9090 ros2-voice-gate
FROM ros:jazzy
RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-jazzy-turtlesim ros-jazzy-rosbridge-suite xvfb \
    && rm -rf /var/lib/apt/lists/*
COPY gate.py /gate.py
EXPOSE 9090
# /ros_entrypoint.sh (from the base image) already sources /opt/ros/jazzy/setup.bash
CMD ros2 launch rosbridge_server rosbridge_websocket_launch.xml & \
    xvfb-run -a ros2 run turtlesim turtlesim_node & \
    exec python3 /gate.py
