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


# from http://d.hatena.ne.jp/hush_puppy/20090226/1235661269
def width_kana(str):
    all = len(str)
    zenkaku = count_zen(str)
    hankaku = all - zenkaku
    return zenkaku * 2 + hankaku


try:
    # FIXME import error?
    import unicodedata

    def count_zen(str):
        n = 0
        for c in str:
            wide_chars = u"WFA"
            eaw = unicodedata.east_asian_width(c)
            if wide_chars.find(eaw) > -1:
                n += 1
        return n
except ImportError:
    def count_zen(str):
        return len(str)


def get_char_width(view):
    r = view.find('.', 0)
    if r is None:
        return 8  # Default char width
    text = view.substr(r)
    p1 = view.text_to_layout(r.begin())
    p2 = view.text_to_layout(r.end())
    assert p1[1] == p2[1]
    width = p2[0] - p1[0]
    count = width_kana(text)
    return width / count


def get_number_column(n):
    return int(math.log10(n)) + 1


def calc_line_numbers_width(view, char_width):
    lines, _ = view.rowcol(view.size())
    c = get_number_column(lines + 1) + 2
    return c * char_width


def get_layout_rowcol(layout):
    c = len(layout['cols']) - 1
    r = len(layout['rows']) - 1
    return (r, c)


def get_group_rowcol(layout, group):
    c = len(layout['cols']) - 1
    return (group // c, group % c)


def make_list2d(lst, cols):
    assert (len(lst) % cols) == 0
    return [lst[i * cols:(i + 1) * cols] for i in range(len(lst) / cols)]


def calc_view_offset(window, layout, extents, group_row, group_col):
    _, c = get_layout_rowcol(layout)
    l2d = make_list2d(extents, c)
    offx = []
    offy = []

    for y in range(group_row):
        offy.append(l2d[y][group_col][1])

    for y in range(group_row + 1):
        if get_setting('imesupport_show_tabs'):
            offy.append(get_setting('imesupport_tabs_height'))

    for x in range(group_col):
        offx.append(l2d[group_row][x][0])
        if get_setting('imesupport_show_minimap'):
            offx.append(get_setting('imesupport_minimap_width'))
        offx.append(get_setting('imesupport_view_frame_right'))

    if window.active_view() is not None:
        char_width = get_char_width(window.active_view())
    else:
        char_width = 0

    for x in range(group_col + 1):
        offx.append(get_setting('imesupport_view_frame_left'))
        group = x + group_row * c
        view = window.active_view_in_group(group)
        if view.settings().get('line_numbers'):
            offx.append(calc_line_numbers_width(view, char_width))
        else:
            offx.append(char_width * 2)

    return offx, offy


def get_current_view_offset(view):
    window = view.window()
    layout = window.get_layout()
    view_groups = [window.active_view_in_group(g) for g in range(window.num_groups())]
    extents = [(0.0, 0.0) if v is None else v.viewport_extent() for v in view_groups]
    row, col = get_group_rowcol(layout, window.active_group())
    return calc_view_offset(window, layout, extents, row, col)


def calc_position(view):
    point = view.sel()[0].a
    abspoint = view.text_to_layout(point)
    offset = view.viewport_position()

    p = sub(abspoint, offset)
    offset = get_current_view_offset(view)
    # TODO it can get 'side_bar_width' from .sublime-workspace
    if get_setting('imesupport_side_bar_visible'):
        offset[0].append(get_setting('imesupport_side_bar_width'))

    offset[0].append(get_setting('imesupport_offset_x'))
    offset[1].append(get_setting('imesupport_offset_y'))
    p = add(p, (sum(offset[0]), sum(offset[1])))

    font_face = view.settings().get('font_face', '')
    font_size = int(view.settings().get('font_size', 11))

    sublime.status_message('IMESupport: ' + str(p) + repr(offset))
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


def update_position(view):
    if not register_callback(view):
        return
    global last_pos
    last_pos = calc_position(view)


class ImeInlineUpdatePositionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        if view.window() is None:
            sublime.status_message('IMESupport: view.window() is None')
            return
        hwnd = view.window().hwnd()

        # FIXME not work If the same file is open in multiple tabs.

        p = calc_position(view)
        set_inline_position(hwnd, int(p[0]), int(p[1]))
        # sublime.status_message('ime_inline_update_position')


class ImeInlineEventListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        update_position(view)

    def on_selection_modified(self, view):
        update_position(view)


class _ImeSupportWindowSetupCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        # print('IMESupport: subclass.setup')
        subclass.setup(window.hwnd(), callback)
        # print('get_char_width', get_char_width(window.active_view()))

    def is_enabled(self):
        return False

    def is_visible(self):
        return False
