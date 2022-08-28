"""Record VALORANT-rank-yoinker's actions and state."""
from glob import glob
from locale import getpreferredencoding
from os import mkdir, getcwd
from time import time, strftime, localtime


# pylint: disable=too-few-public-methods
class Logging:
    """Handles logging vRY's actions and state to the logs' folder."""

    def __init__(self):
        self.log_file_opened = False

    def log(self, string_to_log: str):
        """Creates a folder for and logs the actions and state."""
        try:
            mkdir(getcwd() + r"\logs")
        except FileExistsError:
            pass
        filenames = []
        for filename in glob(r"logs/log-*.txt"):
            filenames.append(int(filename[9:-4]))
        if len(filenames) == 0:
            filenames.append(0)
        if self.log_file_opened:
            with open(f"logs/log-{max(filenames)}.txt",
                      "a", encoding=getpreferredencoding()) as log_file:
                log_file.write(
                    f"[{strftime('%Y.%m.%d-%H.%M.%S', localtime(time()))}]"
                    f" {string_to_log.encode('ascii', 'replace').decode()}\n")
        else:
            with open(f"logs/log-{max(filenames) + 1}.txt",
                      "w", encoding=getpreferredencoding()) as log_file:
                self.log_file_opened = True
                log_file.write(
                    f"[{strftime('%Y.%m.%d-%H.%M.%S', localtime(time()))}]"
                    f" {string_to_log.encode('ascii', 'replace').decode()}\n")
