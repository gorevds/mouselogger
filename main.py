"""

Created by Dmitry Gorev at 04.08.2018
"""

from os import path, mkdir, system
from sys import argv

from utils.mouse_logger import MouseLogger
from utils.install import add_to_startup, remove_from_startup
from utils.archived import all_to_one
from common import LOG_NAME, LOG_DIR, APP_FILE_NAME


def __main():
    if not path.exists(LOG_DIR):
        mkdir(LOG_DIR)

    ml = MouseLogger()
    ml.start()


USAGE = "Usage: MouseLogger.exe {start|install|uninstall}"


def __dispatch(command):
    if command == "start":
        __main()
    elif command == "install":
        add_to_startup()
        __main()
    elif command == "uninstall":
        remove_from_startup()
        all_to_one(LOG_DIR, LOG_NAME)
        system("taskkill /f /im " + APP_FILE_NAME + ".exe")
    else:
        print(USAGE)


if __name__ == '__main__':
    if len(argv) < 2:
        print(USAGE)
    else:
        __dispatch(argv[1])
else:
    raise Exception("Модуль предназначен только для запуска")
