#!/usr/bin/env python3
"""The gate. The model proposes (JSON on /voice_cmd); the gate decides what reaches /turtle1/cmd_vel.

  /voice_cmd  std_msgs/String  {"cmd":"move","dir":"forward","distance":2}
                               {"cmd":"turn","dir":"left","angle":90}
                               {"cmd":"stop"}
  /gate_log   std_msgs/String  {"cmd":"move","verdict":"clamped","note":"distance 100 m -> 3 m","duration":3.0}
  /turtle1/cmd_vel  geometry_msgs/Twist, 10 Hz while a command has time left, then one zero.

Self-check without ROS:  python3 gate.py --test
"""
import json, math, sys

MAX_DIST = 3.0      # m      turtlesim world is 11 x 11
MAX_ANGLE = 180.0   # deg
SPEED = 1.0         # m/s
TURN = math.pi / 2  # rad/s
# ponytail: bounded duration IS the watchdog. No command can run longer than MAX_DIST/SPEED = 3 s,
# so a dropped websocket or a crashed browser stops the robot within 3 s. Add a heartbeat if a
# real robot needs sub-second dead-man behaviour.


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def decide(c):
    """-> (linear, angular, duration_s, verdict, note). verdict in ok | clamped | stop | rejected."""
    cmd = c.get("cmd")
    if c.get("ungated") and cmd in ("move", "turn"):  # DEMO ONLY: the talk's "what if there were no gate?" switch. Real robot: delete.
        k = "distance" if cmd == "move" else "angle"
        try: v = float(c.get(k, 1))
        except (TypeError, ValueError): v = 1.0
        sign = -1.0 if c.get("dir") in ("backward", "right") else 1.0
        if cmd == "move": return sign * SPEED, 0.0, abs(v) / SPEED, "ok", f"NO GATE: {v:g} m, unchecked"
        return 0.0, sign * TURN, math.radians(abs(v)) / TURN, "ok", f"NO GATE: {v:g} deg, unchecked"
    if cmd == "stop":
        return 0.0, 0.0, 0.0, "stop", "stopped"
    if cmd == "move":
        try:
            want = float(c.get("distance", 1))
        except (TypeError, ValueError):
            return 0.0, 0.0, 0.0, "rejected", "distance is not a number"
        if want < 0:
            return 0.0, 0.0, 0.0, "rejected", "negative distance"
        d = clamp(want, 0.0, MAX_DIST)
        sign = -1.0 if c.get("dir") == "backward" else 1.0
        verdict = "clamped" if d != want else "ok"
        note = f"distance {want:g} m -> {d:g} m" if verdict == "clamped" else f"{c.get('dir', 'forward')} {d:g} m"
        return sign * SPEED, 0.0, d / SPEED, verdict, note
    if cmd == "turn":
        try:
            want = float(c.get("angle", 90))
        except (TypeError, ValueError):
            return 0.0, 0.0, 0.0, "rejected", "angle is not a number"
        if want < 0:
            return 0.0, 0.0, 0.0, "rejected", "negative angle"
        a = clamp(want, 0.0, MAX_ANGLE)
        sign = -1.0 if c.get("dir") == "right" else 1.0
        verdict = "clamped" if a != want else "ok"
        note = f"angle {want:g} deg -> {a:g} deg" if verdict == "clamped" else f"{c.get('dir', 'left')} {a:g} deg"
        return 0.0, sign * TURN, math.radians(a) / TURN, verdict, note
    return 0.0, 0.0, 0.0, "rejected", f"unknown command {cmd!r}"


def main():
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
    from geometry_msgs.msg import Twist

    class Gate(Node):
        def __init__(self):
            super().__init__("gate")
            self.vel = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
            self.log = self.create_publisher(String, "/gate_log", 10)
            self.create_subscription(String, "/voice_cmd", self.on_cmd, 10)
            self.twist, self.remaining, self.moving = Twist(), 0.0, False
            self.create_timer(0.1, self.tick)
            self.get_logger().info("gate up: /voice_cmd -> /turtle1/cmd_vel")

        def on_cmd(self, msg):
            try:
                c = json.loads(msg.data)
                assert isinstance(c, dict)
            except Exception:
                c = {"cmd": None}
            lin, ang, dur, verdict, note = decide(c)
            if verdict in ("stop", "rejected"):
                self.remaining = 0.0
                if self.moving:
                    self.vel.publish(Twist()); self.moving = False
            else:
                self.twist = Twist(); self.twist.linear.x = lin; self.twist.angular.z = ang
                self.remaining = dur
                self.tick()  # start now, not at the next timer edge
            out = json.dumps({"cmd": c.get("cmd"), "verdict": verdict, "note": note, "duration": round(dur, 2)})
            self.log.publish(String(data=out)); self.get_logger().info(out)

        def tick(self):
            if self.remaining > 0:
                self.vel.publish(self.twist); self.moving = True
                self.remaining -= 0.1
            elif self.moving:
                self.vel.publish(Twist()); self.moving = False

    rclpy.init(); rclpy.spin(Gate())


if __name__ == "__main__":
    if "--test" in sys.argv:
        assert decide({"cmd": "move", "dir": "forward", "distance": 2}) == (1.0, 0.0, 2.0, "ok", "forward 2 m")
        assert decide({"cmd": "move", "dir": "backward", "distance": 100})[:4] == (-1.0, 0.0, 3.0, "clamped")
        assert decide({"cmd": "turn", "dir": "right", "angle": 90})[:4] == (0.0, -TURN, 1.0, "ok")
        assert decide({"cmd": "turn", "dir": "left", "angle": 720})[2:4] == (2.0, "clamped")
        assert decide({"cmd": "move", "distance": 100, "ungated": True})[2] == 100.0
        assert decide({"cmd": "stop"})[3] == "stop"
        assert decide({"cmd": "fly"})[3] == "rejected"
        assert decide({"cmd": "move", "distance": "lots"})[3] == "rejected"
        assert decide({"cmd": "move", "distance": -1})[3] == "rejected"
        print("ok")
    else:
        main()
