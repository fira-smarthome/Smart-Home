import datetime

import numpy as np

from RobotCode import Code


class RobotHistory:
    def __init__(self):
        super().__init__()
        self.master_history = []
        self.timeElapsed = 0
        self.displayToRecordingLabel = False

    def enqueue(self, data, supervisor):
        record = self.update_master_history(data)
        supervisor.ws.send("historyUpdate", ",".join(record))
        history = ""
        histories = list(reversed(self.master_history))
        for h in range(min(len(histories), 5)):
            history = "[" + histories[h][0] + "] " + histories[h][1] + "\n" + history

        if self.displayToRecordingLabel:
            supervisor.setLabel(2, history, 0.7, 0, 0.05, 0xfbc531, 0.2)

    def update_master_history(self, data):
        time = int(self.timeElapsed)
        minute = str(datetime.timedelta(seconds=time))[2:]
        record = [minute, data]
        self.master_history.append(record)
        return record


class RobotManager:
    def __init__(self):
        self.rotation_field = None
        self.translation_field = None
        self.robot_node = None
        self.history = RobotHistory()

        self._score = 0.0
        self._charge = 100.0

        self.name = ""

        self.robot_stopped_time = 0
        self.stopped = False
        self.stopped_time = None

        self.message = []
        self.map_data = np.array([])

        # self.start_tile = None

        self.is_in_simulation = False

        self.left_exit_tile = False

        self.time_elapsed = 0

        self.code = Code()

    @property
    def position(self) -> list:
        return self.translation_field.getSFVec3f()

    @position.setter
    def position(self, pos: list) -> None:
        self.translation_field.setSFVec3f(pos)

    @property
    def rotation(self) -> list:
        return self.rotation_field.getSFRotation()

    @rotation.setter
    def rotation(self, pos: list) -> None:
        self.rotation_field.setSFRotation(pos)

    def add_node(self, node):
        self.robot_node = node
        self.translation_field = self.robot_node.getField('translation')
        self.rotation_field = self.robot_node.getField('rotation')

    def set_max_velocity(self, vel: float) -> None:
        try:
            self.robot_node.getField('wheel_mult').setSFFloat(vel)
        except:
            print()

    def _is_stopped(self) -> bool:
        vel = self.robot_node.getVelocity()
        return all(abs(ve) < 0.001 for ve in vel)

    def time_stopped(self, supervisor) -> float:
        self.stopped = self._is_stopped()

        if self.stopped_time is None:
            if self.stopped:
                self.stopped_time = supervisor.getTime()
        else:
            if self.stopped:
                current_time = supervisor.getTime()
                self.robot_stopped_time = current_time - self.stopped_time
            else:
                self.stopped_time = None
                self.robot_stopped_time = 0

        return self.robot_stopped_time

    def reset_time_stopped(self):
        self.robot_stopped_time = 0
        self.stopped = False
        self.stopped_time = None

    def increase_score(self, message: str, score: float, supervisor, multiplier=1) -> None:
        point = score * multiplier
        if point > 0.0:
            self.history.enqueue(f"{message} +{point}", supervisor)
        elif point < 0.0:
            self.history.enqueue(f"{message} {point}", supervisor)
        self._score += point
        if self._score < 0:
            self._score = 0

    def set_score(self, message: str, score: float, supervisor) -> None:
        # if point > 0.0:
        #     self.history.enqueue(f"{message} +{point}", supervisor)
        # elif point < 0.0:
        #     self.history.enqueue(f"{message} {point}", supervisor)
        self._score = score
        if self._score < 0:
            self._score = 0

    def get_score(self) -> float:
        return self._score

    def increase_charge(self, charge: float) -> None:
        self._charge += charge
        if self._charge < 0:
            self._charge = 0

    def set_name(self, name: str, supervisor) -> None:
        self.name = name
        supervisor.ws.send("setName", name)

    def set_charge(self, charge: float) -> None:
        self._charge = charge
        if self._charge < 0:
            self._charge = 0

    def get_charge(self) -> float:
        return self._charge

    def set_starting_orientation(self):
        self.rotation = [0, 1, 0, 0]

    def update_elapsed_time(self, timeElapsed: int):
        self.time_elapsed = timeElapsed
        self.history.timeElapsed = timeElapsed
