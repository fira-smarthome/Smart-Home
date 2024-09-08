import sys
import threading
import time
import struct

from controller import Supervisor

import CodeUploader
from FiraWindowSender import FiraWindowSender
from RobotManager import *
from TilesController import *

TIME_STEP = 16

DEFAULT_MAX_VELOCITY = 5.0
DEFAULT_MAX_MULT = 1.0

# States
NOT_STARTED = 0
RUNNING = 1
STOPPED = 2
FINISHED = 3

ROBOT_NAME = "CleanerBot"

DUSTY_COLOR = [.7, .6, .43]
CLEAN_COLOR = [1, 1, 1]


class FiraSupervisor(Supervisor):
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
        self.has_charger = False

        self.in_charging_spot = False

        self.is_robot_initialized = False

        self.max_time = 8 * 60

        if self.getCustomData() != '':
            self.max_time = int(self.getCustomData().split(',')[0])
        self.max_real_world_time = max(self.max_time + 60, int(self.max_time * 1.25))
        self.ws.send("update", str(0) + "," + str(0) + "," + str(self.max_time) + "," + str(0) + "," + str(100))

        self.receiver = self.getDevice('receiver')
        self.receiver.setChannel(1)
        self.receiver.enable(TIME_STEP)

        self.emitter = self.getDevice('emitter')

        self.robot_instance = RobotManager()
        self.robot_instance.code.reset_file(self)

        # Make surface dusty and check for charger
        tiles_cnt = self.getFromDef('SURFACE').getField("children").getCount() - 1
        tile_nodes = self.getFromDef('SURFACE').getField("children")
        for i in range(tiles_cnt):
            tile = tile_nodes.getMFNode(i)
            tile.getField("tileColor").setSFColor(DUSTY_COLOR)
            if not self.has_charger and tile.getField('checkpoint').getSFBool():
                self.has_charger = True

    def game_init(self):

        self.robot = self.getFromDef("ROBOT")
        if self.robot is None:
            self.robot = self.add_robot()

        custom_data_field = self.robot.getField("customData")
        robot_name = custom_data_field.getSFString()
        print(robot_name)

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
        grid = coordination_to_grid(self.robot_instance.position, self)
        children = self.getFromDef("SURFACE").getField("children")

        children.getMFNode(grid)
        tiles_cnt = children.getCount() - 1

        min_distance = sys.float_info.max
        selected_min = (0, 0)

        grid_x = self.getFromDef("SURFACE").getField("children").getMFNode(grid).getField('xPos').getSFInt32()
        grid_z = self.getFromDef("SURFACE").getField("children").getMFNode(grid).getField('zPos').getSFInt32()

        for i in range(tiles_cnt):
            tile = children.getMFNode(i)
            if tile.getField("start").getSFBool():
                x_pos = tile.getField('xPos').getSFInt32()
                z_pos = tile.getField('zPos').getSFInt32()
                distance = math.sqrt(math.pow(x_pos - grid_x, 2) + math.pow(z_pos - grid_z, 2))
                if distance < min_distance:
                    selected_min = (x_pos, z_pos)
                    min_distance = distance

        relocate_position = grid_to_coordination(selected_min[0], selected_min[1], self)

        self.robot_instance.position = [relocate_position[0], -0.01, relocate_position[1]]
        self.robot_instance.rotation = [0, 1, 0, 0]

        self.robot_instance.robot_node.resetPhysics()

        self.emitter.send(struct.pack("c", bytes("L", "utf-8")))

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
            'DEF ROBOT ' + proto_name + ' { translation 1000 1000 1000 rotation 0 1 0 3.1415 name "' + ROBOT_NAME + '" controller "' + controller + '" camera_fieldOfView 1 camera_width 64 camera_height 40 }')
        self.ws.send("robotInSimulation")

        return self.getFromDef("ROBOT")

    def set_robot_starting_position(self):
        starting_tile_node = self.getFromDef("START_TILE")
        # starting_pos = starting_tile_node.getField('translation')

        starting_point_min = self.getFromDef("START_MIN")
        starting_min_pos = starting_point_min.getField("translation")

        starting_point_max = self.getFromDef("START_MAX")
        starting_max_pos = starting_point_max.getField("translation")

        starting_min_pos = starting_min_pos.getSFVec3f()
        starting_max_pos = starting_max_pos.getSFVec3f()
        starting_center_pos = [(starting_max_pos[0] + starting_min_pos[0]) / 2,
                               starting_max_pos[1], (starting_max_pos[2] + starting_min_pos[2]) / 2]

        starting_tile = StartTile([starting_min_pos[0], starting_min_pos[2]],
                                  [starting_max_pos[0], starting_max_pos[2]],
                                  starting_tile_node, center=starting_center_pos, )

        self.robot_instance.start_tile = starting_tile
        self.robot_instance.start_tile.tile_node.getField("start").setSFBool(False)

        self.robot_instance.position = [starting_tile.center[0],
                                        starting_tile.center[1], starting_tile.center[2]]
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

                if self.robot_instance.start_tile is not None:
                    self.robot_instance.start_tile.tile_node.getField("start").setSFBool(True)

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

    def update(self):
        if self.game_state == FINISHED:
            return
        if self.is_last_frame and self.game_state != FINISHED:
            self.robot_instance.set_max_velocity(0)
            self.is_last_frame = -1
            self.game_state = FINISHED

        if self.is_first_frame and self.game_state == RUNNING:
            self.game_init()
            self.robot_instance.increase_score("", 1000, self, 1)

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
            grid = coordination_to_grid(new_position, self)
            floor_node = self.getFromDef("SURFACE").getField("children").getMFNode(grid)

            floor_color = floor_node.getField("tileColor")

            if floor_node.getField('checkpoint').getSFBool():
                self.in_charging_spot = True
            else:
                self.in_charging_spot = False

            if floor_color.getSFColor() == DUSTY_COLOR:
                self.robot_instance.increase_score('',
                                                   int(4000 / self.getFromDef('SURFACE').getField(
                                                       "children").getCount()), self, 1)
                floor_color.setSFColor(CLEAN_COLOR)

            now_score = self.robot_instance.get_score()
            self.elapsed_time = min(self.elapsed_time, self.max_time)

            # Charge
            if self.has_charger:
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
                # print(self.robot_instance.robot_node is Robot)

                self.ws.send("update", str(round(now_score, 2)) + "," + str(int(self.elapsed_time)) + "," + str(
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
