# -*- coding: utf-8 -*-
import math
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


import ctypes
from ctypes import windll, byref
from ctypes import Structure, c_ulong
from ctypes.wintypes import RECT, POINT
from ctypes.wintypes import BYTE, LONG

WM_IME_STARTCOMPOSITION = 0x10D


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, b):
    return (a[0] * b[0], a[1] * b[1])


class COMPOSITIONFORM(Structure):
    _fields_ = [
        ('dwStyle', c_ulong),
        ('ptCurrentPos', POINT),
        ('rcArea', RECT),
    ]


# from http://d.hatena.ne.jp/pipehead/20071210
import sys

(major, platform) = sys.getwindowsversion()[0:4:3]
winNT5OrLater = (platform == 2) and (major >= 5)
LF_FACESIZE = 32


class c_tchar(ctypes._SimpleCData):
    if winNT5OrLater:
        _type_ = 'u'  # c_wchar
    else:
        _type_ = 'c'  # c_char


class LOGFONT(Structure):
    _fields_ = [
        ('lfHeight',         LONG),
        ('lfWidth',          LONG),
        ('lfEscapement',     LONG),
        ('lfOrientation',    LONG),
        ('lfWeight',         LONG),
        ('lfItalic',         BYTE),
        ('lfUnderline',      BYTE),
        ('lfStrikeOut',      BYTE),
        ('lfCharSet',        BYTE),
        ('lfOutPrecision',   BYTE),
        ('lfClipPrecision',  BYTE),
        ('lfQuality',        BYTE),
        ('lfPitchAndFamily', BYTE),
        ('lfFaceName',       c_tchar * LF_FACESIZE)
    ]


def set_inline_position(hwnd, x, y, font_face, font_size):
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

    # AttributeError: function 'ImmSetCompositionFont' not found
    # lf = LOGFONT()
    # lf.lfHeight = font_size
    # lf.lfFaceName = font_face
    # windll.imm32.ImmSetCompositionFont(hIMC, byref(lf))

    windll.imm32.ImmReleaseContext(hwnd, hIMC)


def get_number_column(n):
    return int(math.log10(n)) + 1


def calc_line_numbers_width(view):
    lines, _ = view.rowcol(view.size())
    c = get_number_column(lines + 1)
    return c * get_setting('imesupport_line_numbers_char_width', 6)


def calc_position(view):
    point = view.sel()[0].a
    abspoint = view.text_to_layout(point)
    offset = view.viewport_position()

    # sublime.status_message(str(view.text_to_layout(point)))
    # sublime.status_message(str(view.viewport_position()))

    p = sub(abspoint, offset)
    if view.settings().get('line_numbers'):
        p = add(p, (calc_line_numbers_width(view), 0))
    # TODO it can get 'side_bar_width' from .sublime-workspace
    # p[0] += get_setting('imesupport_default_sidebar_width', 0)

    offset = (
        get_setting('imesupport_view_offset_x', 44),
        get_setting('imesupport_view_offset_y', 36))
    font_face = view.settings().get('font_face', 10)
    font_size = int(view.settings().get('font_size', 10))

    p = add(p, offset)
    sublime.status_message(str(p))
    return (int(p[0]), int(p[1]), font_face, font_size)


def get_setting(key, default=None):
    return sublime.load_settings('IMESupport.sublime-settings').get(key, default)


last_pos = ()

def callback(hwnd, msg, wParam, lParam):
    if msg == WM_IME_STARTCOMPOSITION:
        try:
            if len(last_pos) > 0:
                set_inline_position(hwnd, *last_pos)
        except Exception, e:
            import os
            with open(os.path.expandvars('$HOME/log.txt'), 'a') as f:
                f.write('last_pos: ' + str(last_pos) + '\n')
                f.write('Exception: ' + str(e) + '\n')
    return None


def register_callback(view):
    if view.window() is None:
        sublime.status_message('IMESupport: view.window() is None')
        return False
    subclass.setup(view.window().hwnd(), callback)
    return True


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
        if not register_callback(view):
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
