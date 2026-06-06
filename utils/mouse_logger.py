from ctypes import windll, Structure, c_ulong, byref, c_ushort
from time import time, sleep

from common import LOG_DIR, MOUSELOGGER_FILE
from utils.mouse_log_event import MouseLogEvent

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02

# интервал опроса состояния мыши, секунды
POLL_INTERVAL = 0.02


class POINT(Structure):
    _fields_ = [("x", c_ulong), ("y", c_ulong)]


class MouseLogger:
    def __init__(self):
        self.last_event = None
        self.file = None

    @staticmethod
    def get_mouse_position():
        pt = POINT()
        windll.user32.GetCursorPos(byref(pt))
        return [pt.x, pt.y]

    @staticmethod
    def print_to_consol(action, x, y, t):
        print('{} | x: {} y: {} | {}'.format(action, x, y, t))

    @staticmethod
    def now_ms():
        # полный Unix-таймстамп в миллисекундах
        return round(time() * 1000)

    def add_event(self, event):
        # пропускаем "пустые" такты, когда событие не сформировалось
        if event is None:
            return
        # удаление повторов (равенство по action/x/y, без учёта времени)
        if event == self.last_event:
            return
        self.last_event = event
        # self.print_to_consol(event.action, event.x, event.y, event.timestamp)
        self.file.write(event.to_str())
        self.file.flush()

    def _button_event(self, vk, down_action, up_action, was_down, pos, t):
        # GetKeyState возвращает >2 (старший бит), пока кнопка зажата
        pressed = windll.user32.GetKeyState(vk) > 2
        if pressed and not was_down:
            return MouseLogEvent(down_action, pos[0], pos[1], t), True
        if not pressed and was_down:
            return MouseLogEvent(up_action, pos[0], pos[1], t), False
        return None, was_down

    def start(self):
        windll.user32.GetKeyState.restype = c_ushort

        # держим файл открытым на всю сессию, чтобы не открывать его на каждое событие
        with open(LOG_DIR + MOUSELOGGER_FILE, 'a') as self.file:
            # обозначаем начало сессии нулевыми значениями
            self.add_event(MouseLogEvent("0", 0, 0, self.now_ms()))

            lb_down = False
            rb_down = False

            while True:
                pos = self.get_mouse_position()
                t = self.now_ms()

                # движение фиксируем каждым тактом; повторы отсекает add_event
                self.add_event(MouseLogEvent("M", pos[0], pos[1], t))

                lb_event, lb_down = self._button_event(
                    VK_LBUTTON, "L_D", "L_U", lb_down, pos, t)
                self.add_event(lb_event)

                rb_event, rb_down = self._button_event(
                    VK_RBUTTON, "R_D", "R_U", rb_down, pos, t)
                self.add_event(rb_event)

                sleep(POLL_INTERVAL)
