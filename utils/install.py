import sys
from os import path, remove

from common import APP_FILE_NAME, AUTORUN_DIR


def _app_executable_path():
    # для собранного exe (PyInstaller) реальный путь — в sys.executable;
    # getcwd() брать нельзя: рабочий каталог автозапуска не равен каталогу exe
    if getattr(sys, "frozen", False):
        return sys.executable
    return path.abspath(sys.argv[0])


def _startup_bat_path():
    return path.join(AUTORUN_DIR, APP_FILE_NAME + ".bat")


def add_to_startup():
    exe_path = _app_executable_path()
    with open(_startup_bat_path(), "w") as bat_file:
        bat_file.write('start "" "{}" start\n'.format(exe_path))


def remove_from_startup():
    bat_path = _startup_bat_path()
    # guard: повторный uninstall или uninstall без install не должен падать
    if path.exists(bat_path):
        remove(bat_path)
