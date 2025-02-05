import stat
import glob
import os
import shutil


class Code():
    def __init__(self, keep_control=False):
        self.keepController = keep_control

    def reset_file(self, supervisor, manual=False) -> None:
        path = os.path.dirname(os.path.abspath(__file__))
        if path[-4:] == "game":
            path = os.path.join(path, "controllers/robotCode")
        else:
            path = os.path.join(path, "../robotCode")

        files = glob.glob(os.path.join(path, "*"))
        if self.keepController and not manual:
            if len(files) > 0:
                supervisor.ws.send("loaded")
            return

        for file_path in files:
            if not os.access(file_path, os.W_OK):
                os.chmod(file_path, stat.S_IWUSR)

        shutil.rmtree(path)
        os.mkdir(path)
        with open(os.path.join(path, "robotCode.py"), "w") as f:
            pass

    def reset(self, supervisor) -> None:
        self.reset_file(supervisor, True)
        supervisor.ws.send("unloaded")
