from os import getcwd, remove

from common import APP_FILE_NAME, AUTORUN_DIR


def add_to_startup():
    file_path = getcwd() + '\\' + APP_FILE_NAME + ".exe"
    bat_path = AUTORUN_DIR
    with open(bat_path + '\\' + APP_FILE_NAME + ".bat", "w+") as bat_file:
        bat_file.write('start \"\" \"{}\"'.format(file_path) + ' start')


def remove_from_startup():
    bat_path = AUTORUN_DIR
    remove(bat_path + '\\' + APP_FILE_NAME + ".bat")
