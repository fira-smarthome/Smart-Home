import sys

import CodeUploader
from controller import Supervisor
import threading
import time
from TilesController import *
from RobotManager import *

from FiraWindowSender import FiraWindowSender

TIME_STEP = 16

DEFAULT_MAX_VELOCITY = 5.0
DEFAULT_MAX_MULT = 1.0

# States
NOT_STARTED = 0
RUNNING = 1
STOPPED = 2
FINISHED = 3

ROBOT_NAME = "CleanerBot"

ROBOT1_COLOR = [1, 0, 0]
ROBOT2_COLOR = [0, 0, 1]
CLEAN_COLOR = [1, 1, 1]


class SuperTeamFiraSupervisor(Supervisor):
    def __init__(self):
        super().__init__()

        self.robot = None
        self.robot2 = None

        uploader = threading.Thread(target=CodeUploader.start, daemon=True)
        uploader.start()

        self.c_supervisor = self.getFromDef("VACCUMSUPERVISOR")
        self.ws = FiraWindowSender(self)
        self.ws.send("startup")

        self.game_state = NOT_STARTED
        self.is_last_frame = False
        self.is_first_frame = True
        self.elapsed_time = 0
        self.last_time = -1
        self.real_elapsed_time = 0
        self.last_real_time = -1
        self.is_first_real_time = True
        self.last_sent_score = 0
        self.last_sent_time = 0
        self.last_sent_real_time = 0

        self.is_robot_initialized = False

        self.max_time = 8 * 60

        if self.getCustomData() != '':
            self.max_time = int(self.getCustomData().split(',')[0])
        self.max_real_world_time = max(self.max_time + 60, int(self.max_time * 1.25))
        self.ws.send("update", str(0) + "," + str(0) + "," + str(self.max_time) + "," + str(0) + "," + str(100))

        self.receiver = self.getDevice('receiver')
        self.receiver.enable(TIME_STEP)

        self.emitter = self.getDevice('emitter')

        self.robot_instance = RobotManager()
        # self.robot_instance.code.reset_file(self)

        self.robot_instance2 = RobotManager()
        # self.robot_instance2.code.reset_file(self)

    def game_init(self):

        self.robot = self.add_robot(1)
        self.robot2 = self.add_robot(2)

        self.robot_instance.add_node(self.robot)
        self.robot_instance2.add_node(self.robot2)

        self.set_robot_starting_position(1, self.robot_instance)
        self.set_robot_starting_position(2, self.robot_instance2)
        self.robot_instance.is_in_simulation = True
        self.robot_instance2.is_in_simulation = True
        self.robot_instance.set_max_velocity(DEFAULT_MAX_MULT)
        self.robot_instance2.set_max_velocity(DEFAULT_MAX_MULT)

        self.robot_instance.robot_node.resetPhysics()
        self.robot_instance2.robot_node.resetPhysics()

        self.last_time = self.getTime()
        self.is_first_frame = False
        self.is_robot_initialized = True

        self.last_real_time = time.time()

    def relocate_robot(self, r, num):

        starting_point_min = self.getFromDef("START_MIN" + str(num))
        starting_min_pos = starting_point_min.getField("translation")

        starting_point_max = self.getFromDef("START_MAX" + str(num))
        starting_max_pos = starting_point_max.getField("translation")

        starting_min_pos = starting_min_pos.getSFVec3f()
        starting_max_pos = starting_max_pos.getSFVec3f()
        starting_center_pos = [(starting_max_pos[0] + starting_min_pos[0]) / 2,
                               (starting_max_pos[2] + starting_min_pos[2]) / 2]

        r.position = [starting_center_pos[0], -0.01, starting_center_pos[1]]
        r.rotation = [0, 1, 0, 0]

        r.robot_node.resetPhysics()

        self.emitter.send(struct.pack("c", bytes("L", "utf-8")))

        r.increase_score("Lack of Progress", -5, self)

    def robot_quit(self, num, r, timeup):
        if r.is_in_simulation:
            r.robot_node.remove()
            r.is_in_simulation = False
            self.ws.send("robotNotInSimulation" + str(num))
            if not timeup:
                r.history.enqueue("Successful Exit", self)

    def add_robot(self, num):
        controller = "robotCode" + str(num)
        root = self.getRoot()
        root_children_field = root.getField('children')
        root_children_field.importMFNodeFromString(
            -1,
            'DEF ROBOT' + str(
                num) + ' U14 { translation 1000 1000 1000 rotation 0 1 0 3.1415 name "' + ROBOT_NAME + str(
                num) + '" controller "' + controller + '" }')
        self.ws.send("robotInSimulation")

        return self.getFromDef("ROBOT" + str(num))

    def set_robot_starting_position(self, num, r):
        starting_tile_node = self.getFromDef("START_TILE" + str(num))
        # starting_pos = starting_tile_node.getField('translation')

        starting_point_min = self.getFromDef("START_MIN" + str(num))
        starting_min_pos = starting_point_min.getField("translation")

        starting_point_max = self.getFromDef("START_MAX" + str(num))
        starting_max_pos = starting_point_max.getField("translation")

        starting_min_pos = starting_min_pos.getSFVec3f()
        starting_max_pos = starting_max_pos.getSFVec3f()
        starting_center_pos = [(starting_max_pos[0] + starting_min_pos[0]) / 2,
                               starting_max_pos[1], (starting_max_pos[2] + starting_min_pos[2]) / 2]

        starting_tile = StartTile([starting_min_pos[0], starting_min_pos[2]],
                                  [starting_max_pos[0], starting_max_pos[2]],
                                  starting_tile_node, center=starting_center_pos, )

        r.start_tile = starting_tile
        # r.start_tile.tile_node.getField("start").setSFBool(False)

        r.position = [starting_tile.center[0],
                      starting_tile.center[1], starting_tile.center[2]]
        r.set_starting_orientation()

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
                self.robot_quit(0, self.robot_instance, False)
                self.robot_quit(0, self.robot_instance2, False)

                self.simulationReset()
                self.game_state = FINISHED

                self.c_supervisor.restartController()

                if self.robot_instance.start_tile is not None:
                    self.robot_instance.start_tile.tile_node.getField("start").setSFBool(True)
                if self.robot_instance2.start_tile is not None:
                    self.robot_instance2.start_tile.tile_node.getField("start").setSFBool(True)

                self.worldReload()

            if parts[0] == "robotUnload1":
                if self.game_state == NOT_STARTED:
                    self.robot_instance.code.reset(self)
            if parts[0] == "robotUnload2":
                if self.game_state == NOT_STARTED:
                    self.robot_instance2.code.reset(self)

            if parts[0] == 'relocate':
                self.relocate_robot(self.robot_instance, 1)
                self.relocate_robot(self.robot_instance2, 2)

            if parts[0] == 'quit':
                if self.game_state == RUNNING:
                    self.robot_instance.history.enqueue("Give up!", self)
                    self.robot_quit(0, True)
                    self.game_state = FINISHED
                    self.is_last_frame = True
                    self.ws.send("ended")

            if parts[0] == 'rw_reload':
                self.ws.send_all()

            if parts[0] == 'loadControllerPressed1':
                self.ws.update_history("loadControllerPressed1")
            if parts[0] == 'loadControllerPressed2':
                self.ws.update_history("loadControllerPressed2")
            if parts[0] == 'unloadControllerPressed1':
                self.ws.update_history("unloadControllerPressed1")
            if parts[0] == 'unloadControllerPressed2':
                self.ws.update_history("unloadControlerPressed2")

    def update(self):
        if self.is_last_frame and self.game_state != FINISHED:
            self.robot_instance.set_max_velocity(0)
            self.robot_instance2.set_max_velocity(0)
            self.is_last_frame = -1
            self.game_state = FINISHED

        if self.is_first_frame and self.game_state == RUNNING:
            self.game_init()

        if self.robot_instance.is_in_simulation:
            self.robot_instance.update_elapsed_time(self.elapsed_time)
            self.robot_instance2.update_elapsed_time(self.elapsed_time)

            if self.receiver.getQueueLength() > 0:
                received_data = self.receiver.getBytes()
                self.robot_instance.set_message(received_data)
                self.robot_instance2.set_message(received_data)
                self.receiver.nextPacket()

                if self.robot_instance.message:
                    message = self.robot_instance.message
                    # Write a function to process the message

            if self.game_state == RUNNING:
                if self.robot_instance.time_stopped(self) >= 4:
                    self.relocate_robot(self.robot_instance, 1)
                    self.robot_instance.reset_time_stopped()
                if self.robot_instance.position[1] < -0.045 and self.game_state == RUNNING:
                    self.relocate_robot(self.robot_instance, 1)
                    self.robot_instance.reset_time_stopped()

                if self.robot_instance2.time_stopped(self) >= 4:
                    self.relocate_robot(self.robot_instance2, 2)
                    self.robot_instance.reset_time_stopped()
                if self.robot_instance2.position[1] < -0.045 and self.game_state == RUNNING:
                    self.relocate_robot(self.robot_instance2, 2)
                    self.robot_instance2.reset_time_stopped()

        if self.is_robot_initialized:

            new_position = self.robot_instance.position
            grid = coordination_to_grid(new_position, self)
            floor_node = self.getFromDef("SURFACE").getField("children").getMFNode(grid)
            floor_color = floor_node.getField("tileColor")
            floor_color.setSFColor(ROBOT1_COLOR)

            new_position2 = self.robot_instance2.position
            grid2 = coordination_to_grid(new_position2, self)
            floor_node2 = self.getFromDef("SURFACE").getField("children").getMFNode(grid2)
            floor_color2 = floor_node2.getField("tileColor")
            floor_color2.setSFColor(ROBOT2_COLOR)

            score1 = 0
            score2 = 0
            tiles_cnt = self.getFromDef('SURFACE').getField("children").getCount() - 1
            tile_nodes = self.getFromDef('SURFACE').getField("children")
            for i in range(tiles_cnt):
                tile = tile_nodes.getMFNode(i)
                color = tile.getField("tileColor").getSFColor()
                if color == ROBOT1_COLOR:
                    score1 += 1
                elif color == ROBOT2_COLOR:
                    score2 += 1
            now_score = score1
            now_score2 = score2
            self.robot_instance.set_score(now_score)
            self.robot_instance2.set_score(now_score2)
            self.ws.send("update", str(round(now_score, 2)) + "," + str(round(now_score2, 2)) + "," + str(
                int(self.max_time)) + "," + str(
                self.elapsed_time))

            self.elapsed_time = min(self.elapsed_time, self.max_time)

            self.real_elapsed_time = min(self.real_elapsed_time, self.max_real_world_time)

            if (((self.elapsed_time >= self.max_time or self.real_elapsed_time >= self.max_real_world_time) and
                 self.is_last_frame != -1)):
                self.robot_quit(0, self.robot_instance, True)
                self.robot_quit(0, self.robot_instance2, True)

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

    firaGame = SuperTeamFiraSupervisor()

    while True:
        firaGame.update()
