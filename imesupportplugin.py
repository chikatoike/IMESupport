# -*- coding: utf-8 -*-
import sublime
import sublime_plugin
from imesupport import subclass


# Memo
# >>> window.get_view_index(view)
# (0, 0)
# only one view
# >>> window.get_layout()
# {'cells': [[0L, 0L, 1L, 1L]], 'rows': [0.0, 1.0], 'cols': [0.0, 1.0]}
# virtical splited two views
# >>> window.get_layout()
# {'cells': [[0L, 0L, 1L, 1L], [1L, 0L, 2L, 1L]], 'rows': [0.0, 1.0], 'cols': [0.0, 0.51641586867305067, 1.0]}
# virtical splited three views
# >>> window.get_layout()
# {'cells': [[0L, 0L, 1L, 1L], [1L, 0L, 2L, 1L], [2L, 0L, 3L, 1L]], 'rows': [0.0, 1.0], 'cols': [0.0, 0.33000000000000002, 0.66000000000000003, 1.0]}


from ctypes import windll, byref
from ctypes.wintypes import RECT, POINT
from ctypes import Structure, c_ulong

WM_IME_STARTCOMPOSITION = 0x10D


def add(pos, factor):
    return (pos[0] + factor[0], pos[1] + factor[1])


def sub(pos, factor):
    return (pos[0] - factor[0], pos[1] - factor[1])


def mul(pos, factor):
    return (pos[0] * factor[0], pos[1] * factor[1])


class COMPOSITIONFORM(Structure):
    _fields_ = [
        ("dwStyle", c_ulong),
        ("ptCurrentPos", POINT),
        ("rcArea", RECT),
    ]


def set_inline_position(hwnd, x, y):
    # borrowed from http://d.hatena.ne.jp/doloopwhile/20090627/1275176169
    hIMC = windll.imm32.ImmGetContext(hwnd)
    status = windll.imm32.ImmGetOpenStatus(hIMC)
    if not status:
        windll.imm32.ImmReleaseContext(hwnd, hIMC)
        return

    pt = POINT(x, y)
    cf = COMPOSITIONFORM()
    cf.dwStyle = 2      # CFS_POINT
    cf.ptCurrentPos = pt
    windll.imm32.ImmSetCompositionWindow(hIMC, byref(cf))
    windll.imm32.ImmReleaseContext(hwnd, hIMC)


def calc_position(view):
    point = view.sel()[0].a
    abspoint = view.text_to_layout(point)
    offset = view.viewport_position()

    # sublime.status_message(str(view.text_to_layout(point)))
    # sublime.status_message(str(view.viewport_position()))

    p = sub(abspoint, offset)
    # sublime.status_message(str(p))

    offset = (
        get_setting("sublimeimeinline_view_offset_x", 30),
        get_setting("sublimeimeinline_view_offset_y", 50))

    p = add(p, offset)
    # sublime.status_message(str(p))
    return (int(p[0]), int(p[1]))


def get_setting(key, default=None):
    try:
        s = sublime.load_settings("IMESupport.sublime-settings")
        return s.get(key, default)
    except:
        return default


last_pos = (0, 0)

def callback(hwnd, msg, wParam, lParam):
    if msg == WM_IME_STARTCOMPOSITION:
        set_inline_position(hwnd, last_pos[0], last_pos[1])
        import os
        with open(os.path.expandvars('$HOME/log.txt'), 'a') as f:
            f.write('last_pos: ' + str(last_pos) + '\n')
    return None


class ImeInlineUpdatePositionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        if view.window() is None:
            sublime.status_message('IMESupport: view.window() is None')
            return
        hwnd = view.window().hwnd()

        p = calc_position(view)
        set_inline_position(hwnd, int(p[0]), int(p[1]))
        # sublime.status_message('ime_inline_update_position')


class ImeInlineEventListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        if view.window() is None:
            sublime.status_message('IMESupport: view.window() is None')
            return

        global last_pos
        last_pos = calc_position(view)


class _ImeSupportWindowSetupCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        print('IMESupport: subclass.setup')
        subclass.setup(window.hwnd(), callback)

    def is_enabled(self):
        return False

    def is_visible(self):
        return False
