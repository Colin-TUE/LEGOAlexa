#!/usr/bin/env python3
# Copyright 2019 Colin.  All Rights Reserved.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMAZON SPECIFICALLY DISCLAIMS, WITH 
# RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING 
# THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.

import os
import sys
import time
import logging
import json
import random
import threading

from enum import Enum
from agt import AlexaGadget

from ev3dev2.led import Leds
from ev3dev2.sound import Sound
from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, MoveTank, SpeedPercent, MediumMotor, LargeMotor
from ev3dev2.sensor.lego import InfraredSensor

# Set the logging level to INFO to see messages from AlexaGadget
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(message)s')
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger = logging.getLogger(__name__)


class Direction(Enum):
    """
    The list of directional commands and their variations.
    These variations correspond to the skill slot values.
    """
    FORWARD = ['forward', 'forwards', 'go forward', 'north']
    BACKWARD = ['back', 'backward', 'backwards', 'go backward', 'south']
    LEFT = ['left', 'go left', 'east']
    RIGHT = ['right', 'go right', 'west']
    FORWARD_LEFT = ['north west', 'forward left']
    FORWARD_RIGHT = ['north east', 'forward right']
    BACKWARD_LEFT = ['south west', 'backward left']
    BACKWARD_RIGHT = ['south east', 'backward right']
    ROTATE_LEFT = ['left', 'counterclockwise', 'anticlockwise']
    ROTATE_RIGHT = ['right', 'clockwise']
    STOP = ['stop', 'brake']


class Command(Enum):
    """
    The list of preset commands and their invocation variation.
    These variations correspond to the skill slot values.
    """
    MOVE_CIRCLE = ['circle', 'spin']
    MOVE_SQUARE = ['square']
    PATROL = ['patrol']
    SHOOT = ['shoot']
    TAKE = ['take']

class EventName(Enum):
    """
    The list of custom event name sent from this gadget
    """
    CLOSING = "Closing"
    SCORE = "Score"
    TAKING = "Taking"

class MindstormsGadget(AlexaGadget):
    """
    A Mindstorms gadget that performs movement based on voice commands.
    Two types of commands are supported, directional movement and preset.
    """

    def __init__(self):
        """
        Performs Alexa Gadget initialization routines and ev3dev resource allocation.
        """
        super().__init__()

        # Gadget state
        self.scoring_mode = False
        self.patrol_mode = False
        self.taking_mode = False
        self.closing = False

        # Ev3dev initialization
        self.leds = Leds()
        self.sound = Sound()
        self.motorLeft = LargeMotor(OUTPUT_A)
        self.motorRight = LargeMotor(OUTPUT_B)
        self.motorBack = LargeMotor(OUTPUT_C)
        self.motorBall = MediumMotor(OUTPUT_D)
        self.ir = InfraredSensor()

        # Start threads
        threading.Thread(target=self._patrol_thread, daemon=True).start()
        threading.Thread(target=self._proximity_thread, daemon=True).start()
        threading.Thread(target=self._take_stop_thread, daemon=True).start()

    def on_connected(self, device_addr):
        """
        Gadget connected to the paired Echo device.
        :param device_addr: the address of the device we connected to
        """
        self.leds.set_color("LEFT", "GREEN")
        self.leds.set_color("RIGHT", "GREEN")
        logger.info("{} connected to Echo device".format(self.friendly_name))

    def on_disconnected(self, device_addr):
        """
        Gadget disconnected from the paired Echo device.
        :param device_addr: the address of the device we disconnected from
        """
        self.leds.set_color("LEFT", "BLACK")
        self.leds.set_color("RIGHT", "BLACK")
        logger.info("{} disconnected from Echo device".format(self.friendly_name))

    def on_custom_mindstorms_gadget_control(self, directive):
        """
        Handles the Custom.Mindstorms.Gadget control directive.
        :param directive: the custom directive with the matching namespace and name
        """
        try:
            payload = json.loads(directive.payload.decode("utf-8"))
            print("Control payload: {}".format(payload), file=sys.stderr)
            control_type = payload["type"]
            if control_type == "move":
                # Expected params: [direction, duration, speed]
                self._move(payload["direction"], int(payload["duration"]), int(payload["speed"]))

            if control_type == "rotate":
                # Expected params: [rotation, duration, speed]
                self._turn(payload["rotation"], int(payload["duration"]), int(payload["speed"]))

            if control_type == "command":
                # Expected params: [command]
                self._activate(payload["command"])

        except KeyError:
            print("Missing expected parameters: {}".format(directive), file=sys.stderr)

    def _move(self, direction, duration: int, speed: int, is_blocking=False):
        """
        Handles move commands from the directive.
        Right and left movement can under or over turn depending on the surface type.
        :param direction: the move direction
        :param duration: the duration in seconds
        :param speed: the speed percentage as an integer
        :param is_blocking: if set, motor run until duration expired before accepting another command
        """
        print("Move command: ({}, {}, {}, {})".format(direction, speed, duration, is_blocking), file=sys.stderr)
        if direction in Direction.FORWARD.value:
            self.motorLeft.on_for_seconds(SpeedPercent(speed), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(-speed), duration, block=is_blocking)

        if direction in Direction.BACKWARD.value:
            self.motorLeft.on_for_seconds(SpeedPercent(-speed), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(speed), duration, block=is_blocking)

        if direction in Direction.RIGHT.value:
            self.motorLeft.on_for_seconds(SpeedPercent(-speed/2), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(-speed/2), duration, block=is_blocking)
            self.motorBack.on_for_seconds(SpeedPercent(speed), duration, block=is_blocking)

        if direction in Direction.LEFT.value:
            self.motorLeft.on_for_seconds(SpeedPercent(speed/2), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(speed/2), duration, block=is_blocking)
            self.motorBack.on_for_seconds(SpeedPercent(-speed), duration, block=is_blocking)
        
        if direction in Direction.FORWARD_RIGHT.value:
            self.motorLeft.on_for_seconds(SpeedPercent(speed/4), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(-speed), duration, block=is_blocking)
            self.motorBack.on_for_seconds(SpeedPercent(speed/2), duration, block=is_blocking)

        if direction in Direction.BACKWARD_RIGHT.value:
            self.motorLeft.on_for_seconds(SpeedPercent(-speed), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(speed/4), duration, block=is_blocking)
            self.motorBack.on_for_seconds(SpeedPercent(speed/2), duration, block=is_blocking)

        if direction in Direction.FORWARD_LEFT.value:
            self.motorLeft.on_for_seconds(SpeedPercent(speed), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(-speed/4), duration, block=is_blocking)
            self.motorBack.on_for_seconds(SpeedPercent(-speed/2), duration, block=is_blocking)

        if direction in Direction.BACKWARD_LEFT.value:
            self.motorLeft.on_for_seconds(SpeedPercent(-speed/4), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(speed), duration, block=is_blocking)
            self.motorBack.on_for_seconds(SpeedPercent(-speed/2), duration, block=is_blocking)

        if direction in Direction.STOP.value:
            self.motorLeft.off()
            self.motorRight.off()
            self.motorBack.off()
            self.patrol_mode = False

    def _activate(self, command, speed=50):
        """
        Handles preset commands.
        :param command: the preset command
        :param speed: the speed if applicable
        """
        print("Activate command: ({}, {})".format(command, speed), file=sys.stderr)
        if command in Command.MOVE_CIRCLE.value:
            self._move("right", 2, speed)
            self._move("forward", 2, speed)
            self._move("left", 2, speed)
            self._move("backward", 2, speed)

        if command in Command.MOVE_SQUARE.value:
            for i in range(4):
                self._move("forward", 2, speed)
                self._turn("left", 1, speed)

        if command in Command.PATROL.value:
            # Set patrol mode to resume patrol thread processing
            self.patrol_mode = True

        if command in Command.SHOOT.value:
            self.motorBall.on_for_seconds(SpeedPercent(-50), 0.2)
            if self.scoring_mode and self.closing:
                self._send_event(EventName.SCORE, {})                

            self.leds.set_color("LEFT", "GREEN", 1)
            self.leds.set_color("RIGHT", "GREEN", 1)

            self.scoring_mode = False
            self.closing = False

        if command in Command.TAKE.value:
            self.motorBall.on(SpeedPercent(5))
            self.taking_mode = True

    def _turn(self, direction, duration, speed, is_blocking=False):
        """
        Turns based on the specified direction and speed.
        Calibrated for hard smooth surface.
        :param direction: the turn direction
        :param duration: the turn duration in seconds
        :param speed: the turn speed
        :param is_blocking: if set, motor run until duration expired before accepting another command
        """
        if direction in Direction.LEFT.value:
            self.motorLeft.on_for_seconds(SpeedPercent(speed/5), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(speed/5), duration, block=is_blocking)
            self.motorBack.on_for_seconds(SpeedPercent(speed/5), duration, block=is_blocking)

        if direction in Direction.RIGHT.value:
            self.motorLeft.on_for_seconds(SpeedPercent(-speed/5), duration, block=is_blocking)
            self.motorRight.on_for_seconds(SpeedPercent(-speed/5), duration, block=is_blocking)
            self.motorBack.on_for_seconds(SpeedPercent(-speed/5), duration, block=is_blocking)

    def _send_event(self, name: EventName, payload):
        """
        Sends a custom event to trigger a sentry action.
        :param name: the name of the custom event
        :param payload: the sentry JSON payload
        """
        self.send_custom_event('Custom.Mindstorms.Gadget', name.value, payload)

    def _patrol_thread(self):
        """
        Performs random movement when patrol mode is activated.
        """
        while True:
            while self.patrol_mode:
                print("Patrol mode activated randomly picks a path", file=sys.stderr)
                direction = random.choice(list(Direction))
                duration = random.randint(1, 5)
                speed = random.randint(1, 4) * 25

                while direction == Direction.STOP:
                    direction = random.choice(list(Direction))

                # direction: all except stop, duration: 1-5s, speed: 25, 50, 75, 100
                self._move(direction.value[0], duration, speed)
                time.sleep(duration)
            time.sleep(1)

    def _proximity_thread(self):
        """
        Monitors the distance between the robot and an obstacle when sentry mode is activated.
        If the minimum distance is breached, send a custom event to trigger action on
        the Alexa skill.
        """
        count = 0
        while True:
            while self.scoring_mode:
                distance = self.ir.proximity
                # print("Proximity: {}".format(distance), file=sys.stderr)
                count = count + 1 if distance < 50 else 0
                if count > 3:
                    print("Closing in. Sending event to skill", file=sys.stderr)
                    self.leds.set_color("LEFT", "RED", 1)
                    self.leds.set_color("RIGHT", "RED", 1)

                    self._send_event(EventName.CLOSING, {'distance': distance})
                    self.closing = True
                    break

                time.sleep(0.2)
            time.sleep(1)

    def _take_stop_thread(self):
        """
        Monitors the power used by the motorBall motor
        """
        count = 0
        while True:
            while self.taking_mode:
                power = self.motorBall.duty_cycle
                print("Duty Cycle: {}".format(power), file=sys.stderr)
                count = count + 1 if power > 40 else 0
                if count > 3:
                    print("Took the ball. Sending event to skill", file=sys.stderr)
                    self.leds.set_color("LEFT", "YELLOW", 1)
                    self.leds.set_color("RIGHT", "YELLOW", 1)

                    self._send_event(EventName.TAKING, {})
                    self.motorBall.stop()
                    self.taking_mode = False
                    self.scoring_mode = True

                time.sleep(0.2)
            time.sleep(1)


if __name__ == '__main__':

    gadget = MindstormsGadget()

    # Set LCD font and turn off blinking LEDs
    os.system('setfont Lat7-Terminus12x6')
    gadget.leds.set_color("LEFT", "BLACK")
    gadget.leds.set_color("RIGHT", "BLACK")

    # Startup sequence
    gadget.sound.play_song((('C4', 'e'), ('D4', 'e'), ('E5', 'q')))
    gadget.leds.set_color("LEFT", "GREEN")
    gadget.leds.set_color("RIGHT", "GREEN")

    # Gadget main entry point
    gadget.main()

    # Shutdown sequence
    gadget.sound.play_song((('E5', 'e'), ('C4', 'e')))
    gadget.leds.set_color("LEFT", "BLACK")
    gadget.leds.set_color("RIGHT", "BLACK")
