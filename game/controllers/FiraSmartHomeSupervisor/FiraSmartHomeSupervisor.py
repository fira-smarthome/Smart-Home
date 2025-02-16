import json
import math
import os
import sys
import threading
import time

import numpy as np
from PIL import Image, ImageDraw
from controller import Supervisor

import CodeUploader
from FiraWindowSender import FiraWindowSender
from RobotManager import *
from Room import House, Room

TIME_STEP = 16
MAP_WIDTH = 2.56

DEFAULT_MAX_VELOCITY = 10.0
DEFAULT_MAX_MULT = 1.0

MODIFIED_TEXTURE_PATH1 = "/protos/textures/modified_paint_texture1.png"
MODIFIED_TEXTURE_PATH2 = "/protos/textures/modified_paint_texture2.png"
UNMODIFIED_TEXTURE_PATH = "/protos/textures/surface_start.png"

# States
NOT_STARTED = 0
RUNNING = 1
STOPPED = 2
FINISHED = 3

ROBOT_NAME = "CleanerBot"


class FiraSupervisor(Supervisor):

    def debug(self, *args):
        if self.verbose:
            print(args)

    def __init__(self):
        super().__init__()

        self.robot = None

        uploader = threading.Thread(target=CodeUploader.start, daemon=True)
        uploader.start()

        self.c_supervisor = self.getFromDef("VACCUMSUPERVISOR")
        if self.c_supervisor is None:
            self.c_supervisor = self.getFromDef("MAINSUPERVISOR")
        self.ws = FiraWindowSender(self)
        self.ws.send("startup")

        game_info = self.getFromDef('Info')

        self.verbose = game_info.getField('verbose').getSFBool()

        self.send_room_data = game_info.getField('send_room_data').getSFBool()

        rooms_count = game_info.getField('rooms_count').getSFInt32()
        self.house = House()
        for i in range(rooms_count):
            count = game_info.getField(f'room{i + 1}_count').getSFInt32()
            points = []
            for ii in range(count):
                points.append(game_info.getField(f'room{i + 1}').getMFVec2f(ii))
            self.house.add_room(Room(f"Room {i + 1}", [(ii[0], ii[1]) for ii in points]))

        charger_count = game_info.getField('charging_points_count').getSFInt32()
        self.charging_points = []
        for i in range(charger_count):
            self.charging_points.append(game_info.getField('charging_points').getMFVec2f(i))
        self.debug("Charging Points: ", self.charging_points)

        relocation_count = game_info.getField('relocation_points_count').getSFInt32()
        self.relocation_points = []
        for i in range(relocation_count):
            self.relocation_points.append(game_info.getField('relocation_points').getMFVec2f(i))
        self.debug("Relocation Points: ", self.relocation_points)

        self.start_point = game_info.getField('start_point').getSFVec3f()
        self.debug("Start Point: ", self.start_point)

        self.game_state = NOT_STARTED
        self.is_last_frame = False
        self.is_first_frame = True
        self.elapsed_time = 0
        self.last_elapsed_time = 0
        self.last_time = -1
        self.real_elapsed_time = 0
        self.last_real_time = -1
        self.is_first_real_time = True
        self.last_sent_score = 0
        self.last_sent_time = 0
        self.last_sent_real_time = 0
        self.last_robot_position = None
        self.last_charging_state = False
        self.has_charger = len(self.charging_points) > 0

        self.in_charging_spot = False

        self.is_robot_initialized = False

        self.max_time = 8 * 60

        self.score_history = []

        if self.getCustomData() != '':
            self.max_time = int(self.getCustomData().split(',')[0])
        self.max_real_world_time = max(self.max_time + 60, int(self.max_time * 1.25))
        self.ws.send("update", str(0) + "," + str(0) + "," + str(self.max_time) + "," + str(0) + "," + str(100))

        self.receiver = self.getDevice('receiver')
        self.receiver.setChannel(1)
        self.receiver.enable(TIME_STEP)

        self.emitter = self.getDevice('emitter')
        self.emitter.setChannel(1)

        self.robot_instance = RobotManager()
        self.robot_instance.code.reset_file(self)

        self.current_texture = True

        image = Image.open(os.getcwd() + UNMODIFIED_TEXTURE_PATH)

        image.save(os.getcwd() + MODIFIED_TEXTURE_PATH1)
        image.save(os.getcwd() + MODIFIED_TEXTURE_PATH2)

        self.paint_surface_texture(None)

    def game_init(self):

        self.robot = self.getFromDef("ROBOT")
        if self.robot is None:
            self.robot = self.add_robot()

        self.robot_instance.add_node(self.robot)

        self.set_robot_starting_position()
        self.robot_instance.is_in_simulation = True
        self.robot_instance.set_max_velocity(DEFAULT_MAX_MULT)

        self.robot_instance.robot_node.resetPhysics()

        self.last_time = self.getTime()
        self.is_first_frame = False
        self.is_robot_initialized = True

        self.last_real_time = time.time()

    def relocate_robot(self, decrease_score=True):
        min_distance = sys.float_info.max
        selected_min = (0, 0)
        current_pos = self.robot_instance.position
        for i in self.relocation_points:
            distance = math.sqrt(math.pow(current_pos[0] - i[0], 2) + math.pow(current_pos[2] - i[1], 2))
            if distance < min_distance:
                selected_min = (i[0], i[1])
                min_distance = distance

        self.robot_instance.position = [selected_min[0], -0.01, selected_min[1]]
        self.robot_instance.rotation = [0, 1, 0, 0]

        self.robot_instance.robot_node.resetPhysics()

        if decrease_score:
            self.robot_instance.increase_score("Lack of Progress", -5, self)
        else:
            self.robot_instance.history.enqueue('Robot Relocated', self)

    def robot_quit(self, num, timeup):
        if self.robot_instance.is_in_simulation:
            self.robot_instance.robot_node.remove()
            self.robot_instance.is_in_simulation = False
            self.ws.send("robotNotInSimulation" + str(num))
            if not timeup:
                self.robot_instance.history.enqueue("Successful Exit", self)

    def add_robot(self):
        controller = "robotCode"
        root = self.getRoot()
        root_children_field = root.getField('children')
        if self.has_charger:
            proto_name = 'U19'
        else:
            proto_name = 'U14'
        root_children_field.importMFNodeFromString(
            -1,
            f'DEF ROBOT {proto_name} {{ translation {self.start_point[0]} {self.start_point[1]} '
            f'{self.start_point[2]} rotation 0 1 0 3.1415 name "{ROBOT_NAME}" controller "{controller}"}}')
        self.ws.send("robotInSimulation")

        return self.getFromDef("ROBOT")

    def get_white_percentage(self, image):
        arr = np.array(image, dtype=np.uint8)

        is_white = (arr[:, :, :3] == 255).all(axis=-1)

        # Calculate percentage (handle empty images)
        return is_white.mean() if arr.size > 0 else 0.0

    def draw_charger_and_relocation_points(self, draw: ImageDraw, width: int):
        multiply_factor = width / MAP_WIDTH
        sum_factor = width / 2
        r = 5
        for charge in self.charging_points:
            x = charge[0]
            y = charge[1]
            x *= multiply_factor
            y *= multiply_factor
            x += sum_factor
            y += sum_factor
            draw.rectangle((x - r, y - r, x + r, y + r), fill=(0, 0, 0))
        for relocation in self.relocation_points:
            x = relocation[0]
            y = relocation[1]
            x *= multiply_factor
            y *= multiply_factor
            x += sum_factor
            y += sum_factor
            draw.rectangle((x - r, y - r, x + r, y + r), fill=(129, 66, 245))

    def paint_surface_texture(self, robot_position):
        if self.current_texture:
            get_path = MODIFIED_TEXTURE_PATH1
            set_path = MODIFIED_TEXTURE_PATH2
        else:
            get_path = MODIFIED_TEXTURE_PATH2
            set_path = MODIFIED_TEXTURE_PATH1
        self.current_texture = not self.current_texture
        surface = self.getFromDef('GROUND')
        image = Image.open(os.getcwd() + get_path)
        width, height = image.size
        multiply_factor = width / MAP_WIDTH
        sum_factor = width / 2

        draw = ImageDraw.Draw(image)
        if robot_position is not None:
            r = 2.5
            x, _, y = robot_position
            x *= multiply_factor
            y *= multiply_factor
            x += sum_factor
            y += sum_factor
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255))

        self.draw_charger_and_relocation_points(draw, width)

        image.save(os.getcwd() + set_path)
        surface.getField("textureUrl").setMFString(0, os.getcwd() + set_path)

        return self.get_white_percentage(image)

    def set_robot_starting_position(self):
        self.robot_instance.position = self.start_point
        self.robot_instance.set_starting_orientation()

    def receive(self, message):

        parts = message.split(",")

        if len(parts) > 0:
            if parts[0] == "run":
                self.game_state = RUNNING
                self.ws.update_history("runPressed")
            if parts[0] == "pause":
                self.game_state = STOPPED
                self.ws.update_history("pausedPressed")
            if parts[0] == "reset":
                self.robot_quit(0, False)

                self.simulationReset()
                self.game_state = FINISHED

                self.c_supervisor.restartController()
                self.worldReload()

            if parts[0] == "robotUnload":
                if self.game_state == NOT_STARTED:
                    self.robot_instance.code.reset(self)

            if parts[0] == 'relocate':
                self.relocate_robot(False)

            if parts[0] == 'quit':
                if self.game_state == RUNNING:
                    self.robot_instance.history.enqueue("Give up!", self)
                    self.robot_quit(0, True)
                    self.game_state = FINISHED
                    self.is_last_frame = True
                    self.ws.send("ended")

            if parts[0] == 'rw_reload':
                self.ws.send_all()

            if parts[0] == 'loadControllerPressed':
                self.ws.update_history("loadControllerPressed")
            if parts[0] == 'unloadControllerPressed':
                self.ws.update_history("unloadControllerPressed")

    def distance(self, robot_position, point) -> float:
        return math.sqrt(math.pow(robot_position[0] - point[0], 2) + math.pow(robot_position[2] - point[1], 2))

    def update(self):
        if self.game_state == FINISHED:
            return

        if self.is_last_frame and self.game_state != FINISHED:
            self.robot_instance.set_max_velocity(0)
            self.is_last_frame = -1
            self.game_state = FINISHED

        if self.is_first_frame and self.game_state == RUNNING:
            self.game_init()

        if self.robot_instance.is_in_simulation:
            self.robot_instance.update_elapsed_time(self.elapsed_time)

            if self.receiver.getQueueLength() > 0:
                received_data = self.receiver.getString()
                if len(received_data) > 0:
                    self.robot_instance.set_name(received_data, self)
                self.receiver.nextPacket()

            if self.game_state == RUNNING:
                if self.robot_instance.time_stopped(self) >= 10:
                    self.relocate_robot(True)
                    self.robot_instance.reset_time_stopped()
                if self.robot_instance.position[1] < -0.045 and self.game_state == RUNNING:
                    self.relocate_robot(True)
                    self.robot_instance.reset_time_stopped()

        if self.is_robot_initialized:

            new_position = self.robot_instance.position
            inside_room = self.house.find_room((new_position[0], new_position[2]))

            if self.has_charger:
                self.emitter.send(str(self.robot_instance.get_charge()).encode('utf-8'))
            elif self.send_room_data:
                self.emitter.send(json.dumps({
                    "current_room": inside_room.name,
                    "cleaning_percentage": self.house.rooms_cleaning_percentages()
                }).encode('utf-8'))

            new_score = self.paint_surface_texture(new_position)
            delta_score = new_score - self.robot_instance.get_score()
            self.house.clean(delta_score, inside_room)

            self.robot_instance.set_score('', new_score, self)

            now_score = self.robot_instance.get_score()

            self.elapsed_time = min(self.elapsed_time, self.max_time)

            # Charge
            if self.has_charger:
                # Calculate distance to each charger
                for charge in self.charging_points:
                    if self.distance(new_position, charge) <= 0.075:
                        self.in_charging_spot = True
                        break
                    else:
                        self.in_charging_spot = False

                if self.in_charging_spot:
                    self.robot_instance.set_charge(100.0)
                    if not self.last_charging_state:
                        self.robot_instance.history.enqueue('Entered Charging Area', self)
                        self.last_charging_state = True
                else:
                    self.robot_instance.increase_charge(-(self.elapsed_time - self.last_elapsed_time) / 2.0)
                    if self.last_charging_state:
                        self.robot_instance.history.enqueue('Exited Charging Area', self)
                        self.last_charging_state = False
            self.last_elapsed_time = self.elapsed_time
            self.real_elapsed_time = min(self.real_elapsed_time, self.max_real_world_time)

            self.last_robot_position = new_position

            if self.last_sent_score != now_score or self.last_sent_time != int(
                    self.elapsed_time) or self.last_sent_real_time != int(self.real_elapsed_time):
                self.score_history.append(str(now_score))

                self.ws.send("setHistoryData", ','.join(self.score_history))

                self.ws.send("update", str(round(now_score * 100, 2)) + "%," + str(int(self.elapsed_time)) + "," + str(
                    self.max_time) + "," + str(int(self.real_elapsed_time)) + "," + str(
                    int(self.robot_instance.get_charge())))
                self.last_sent_score = now_score
                self.last_sent_time = int(self.elapsed_time)
                self.last_sent_real_time = int(self.real_elapsed_time)

            if ((
                    self.elapsed_time >= self.max_time and
                    self.is_last_frame != -1) or
                    self.robot_instance.get_charge() <= 0):
                self.robot_quit(0, self.robot_instance.get_charge() > 0)

                self.game_state = FINISHED
                self.is_last_frame = True

                self.ws.send("ended")

        message = self.wwiReceiveText()
        while message not in ['', None]:
            self.receive(message)
            message = self.wwiReceiveText()

        if self.game_state == STOPPED:
            self.step(0)
            time.sleep(0.01)
            self.last_real_time = time.time()

        if self.is_robot_initialized and self.game_state == RUNNING:
            self.real_elapsed_time += (time.time() - self.last_real_time)
            self.last_real_time = time.time()
            frame_time = self.getTime() - self.last_time
            self.elapsed_time += frame_time
            self.last_time = self.getTime()
            step = self.step(TIME_STEP)
            if step == -1:
                self.game_state = FINISHED

        elif self.is_first_frame or self.is_last_frame or self.game_state == FINISHED:
            self.step(TIME_STEP)


if __name__ == '__main__':
    firaGame = FiraSupervisor()
    while True:
        firaGame.update()
