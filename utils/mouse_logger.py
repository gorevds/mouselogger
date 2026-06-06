from ctypes import windll, Structure, c_ulong, byref, c_ushort
from time import time, sleep

from common import LOG_DIR, MOUSELOGGER_FILE
from utils.mouse_log_event import MouseLogEvent

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02


class POINT(Structure):
    _fields_ = [("x", c_ulong), ("y", c_ulong)]


class MouseLogger:
    def __init__(self):
        self.mouse_log_list = []

    @staticmethod
    def get_mouse_position():
        pt = POINT()
        windll.user32.GetCursorPos(byref(pt))
        return [pt.x, pt.y]

    def print_to_consol(self, action, x, y, t):
        print('{} | x: {} y: {} | {}'.format(action, x, y, t))

    def add_event(self, event):
        # удаление повторов
        if event == self.mouse_log_list[-1]:
            return
        self.mouse_log_list.append(event)
        # self.print_to_consol(event.action, event.x, event.y, event.timestamp)
        with open(LOG_DIR + MOUSELOGGER_FILE, 'a') as file:
            file.write(event.to_str())

    def start(self):
        # обозначаем начало сессии нулевыми значениями
        event = MouseLogEvent("0", 0, 0, 0)
        self.mouse_log_list.append(event)
        with open(LOG_DIR + MOUSELOGGER_FILE, 'a') as file:
            file.write(event.to_str())

        lb_down = False
        rb_down = False

        while True:
            windll.user32.GetKeyState.restype = c_ushort
            pos = self.get_mouse_position()
            
            t = str(round(time() * 1000))[-9:]

            # перехват левой кнопки мыши
            lb = windll.user32.GetKeyState(VK_LBUTTON)
            event = None
            if lb > 2:
                if lb_down:
                    event = MouseLogEvent("M", pos[0], pos[1], t)
                else:
                    event = MouseLogEvent("L_D", pos[0], pos[1], t)
                    lb_down = True

            if lb < 2:
                if not lb_down:
                    event = MouseLogEvent("M", pos[0], pos[1], t)
                else:
                    event = MouseLogEvent("L_U", pos[0], pos[1], t)
                    lb_down = False

            self.add_event(event)

            # перехват правой кнопки мыши
            rb = windll.user32.GetKeyState(VK_RBUTTON)
            if rb > 2:
                if rb_down:
                    event = MouseLogEvent("M", pos[0], pos[1], t)
                else:
                    event = MouseLogEvent("R_D", pos[0], pos[1], t)
                    rb_down = True

            if rb < 2:
                if not rb_down:
                    event = MouseLogEvent("M", pos[0], pos[1], t)
                else:
                    event = MouseLogEvent("R_U", pos[0], pos[1], t)
                    rb_down = False
                    
            self.add_event(event)
            
            sleep(0.02)

