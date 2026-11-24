# ros2-voice-gate

Voice control for ROS 2 that runs in a browser tab, with a safety gate between the model and the robot. No cloud service, no API key, no GPU. Built for the ROSCon India 2026 Demo & Lightning Talk, and tested in simulation (turtlesim) only.

You say "go forward two meters". A small speech model and a small intent model turn it into a command, and the gate decides what actually reaches the robot.

![How it fits together: microphone, Moonshine and Needle 3 in the browser tab, roslibjs over a websocket to rosbridge, gate.py and turtlesim in the Docker container](docs/architecture.png)

## Run it

You need Docker, Python 3 and Chrome.

```sh
git clone https://github.com/nkthakur48/ros2-voice-gate
cd ros2-voice-gate
./vendor.sh                                        # once: downloads the intent model and roslib, about 37 MB
docker build -t ros2-voice-gate .
docker run --rm -p 9090:9090 ros2-voice-gate       # rosbridge + turtlesim + the gate
python3 serve.py                                   # opens http://localhost:8000
```

Wait for **Start microphone** and **rosbridge: connected**, then click Start microphone and speak.

- The page needs internet when it opens: it loads the Moonshine library and downloads the speech model. After that, it works with Wi-Fi off. Do not reload while offline.
- No microphone? Type in the box under the turtle, written like the speech engine writes it: `Move 100 meters.` Arrow keys drive, space stops.
- `?theme=dark` on the address gives the dark theme.

## The gate

The model proposes JSON on `/voice_cmd`. `gate.py` decides what reaches `/turtle1/cmd_vel`:

| Rule | Behaviour |
|---|---|
| Clamp | distance is limited to 3 m, turns to 180° ("move one hundred meters" becomes 3 m) |
| Reject | negative or non-numeric values and unknown commands are dropped |
| Time-box | every move runs for a fixed time, so a dropped connection stops the robot within 3 s |
| Stop | "stop" is matched on the live transcript and skips the model |

`python3 gate.py --test` runs the gate's self-check without ROS. The **Safety gate** checkbox in the page switches the gate off for demonstration only. Delete that path before using the gate on a real robot.

## Status and limits

- Simulation only. Not tested on a real robot.
- Speech errors happen: "drive back three meters" was heard as "forward" (confidence 0.64). The gate cannot catch a command that is valid but wrong, so every command is logged on screen.
- Typed text scores differently from speech. `move one hundred meters` scored 0.38 and sent nothing, `Move 100 meters.` scored 0.80.
- Accents and noisy rooms have not been measured.
- Latency on a laptop (typed input, Node): about 100 to 210 ms per command for the intent model, 2 to 9 ms for the gate round trip.

## Built with

[Moonshine](https://github.com/moonshine-ai/moonshine) speech to text (WASM), Needle 3 intent model on the Cactus runtime, [roslibjs](https://github.com/RobotWebTools/roslibjs), [rosbridge_suite](https://github.com/RobotWebTools/rosbridge_suite), turtlesim, and ROS 2 Jazzy. The turtle and robot artwork is taken from the ROSCon India 2026 logo and is used here for the demo.

## License

Copyright 2026 Nishant Thakur. The code in this repository is released under the [Apache License 2.0](LICENSE).

Not covered by that licence: the dependencies that `vendor.sh` and the page download (Moonshine, Needle 3 and the Cactus runtime, roslibjs), which keep their own licences, and the turtle and robot artwork in `assets/`, which comes from the ROSCon India 2026 logo.
