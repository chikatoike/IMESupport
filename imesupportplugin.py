# -*- coding: utf-8 -*-
import sublime
import sublime_plugin
import math
from imesupport import subclass

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


class WindowLayout(object):
    def __init__(self, window):
        self.window = window
        self.last_extents = None
        self.load_settings()

    def calc_cursor_position(self, view, cursor):
        abspoint = view.text_to_layout(cursor)
        offset = view.viewport_position()
        p = sub(abspoint, offset)

        offset = self.calc_offset(self.window, view)

        if self.side_bar['visible']:
            offset[0].append(self.side_bar['width'])

        offset[0].append(self.get_setting('imesupport_offset_x'))
        offset[1].append(self.get_setting('imesupport_offset_y'))
        p = add(p, (sum(offset[0]), sum(offset[1])))

        font_face = view.settings().get('font_face', '')
        font_size = int(view.settings().get('font_size', 11))

        sublime.status_message('IMESupport: ' + str(p) + repr(offset))
        return (int(p[0]), int(p[1]), font_face, font_size)

    def update_status(self, view=None):
        extents = WindowLayout.get_extent_list(self.window)
        if extents == self.last_extents:
            return  # layout is not changed.
        self.last_extents = extents

        # Get status.
        self.load_settings()
        self.get_status(view)

    def get_status(self, view=None):
        window = self.window
        if view is None:
            view = window.active_view()
            if view is None:
                return None

        self.tabs = WindowLayout.tabs_status(window, view)
        self.minimap = WindowLayout.minimap_status(window, view)
        self.line_numbers = WindowLayout.line_numbers_status(view)
        self.hscroll_bar = WindowLayout.hscroll_bar_status(view)

        # Required self.minimap, self.line_numbers
        self.side_bar = self.side_bar_status(window)

        return {
            'tabs': self.tabs,
            'minimap': self.minimap,
            'line_numbers': self.line_numbers,
            'hscroll_bar': self.hscroll_bar,
            'side_bar': self.side_bar,
            }

    def load_settings(self):
        self.settings = sublime.load_settings('IMESupport.sublime-settings')

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def calc_offset(self, window, view):
        window = self.window
        group, _ = window.get_view_index(view)
        layout = window.get_layout()

        _, c = WindowLayout.get_layout_rowcol(layout)
        g2d = WindowLayout.make_list2d(WindowLayout.get_group_list(window), c)
        row, col = WindowLayout.get_group_rowcol(layout, group)

        offset = [[], []]
        offset[0] += self.calc_group_offset_width(g2d, col)
        offset[1] += self.calc_group_offset_height(g2d, row)
        offset[0] += self.calc_view_width_offset(view)
        offset[1] += self.calc_view_height_offset(view)
        return offset

    def side_bar_status(self, window):
        window = self.window
        layout = window.get_layout()

        r, c = WindowLayout.get_layout_rowcol(layout)
        g2d = WindowLayout.make_list2d(WindowLayout.get_group_list(window), c)

        offset1 = self.calc_group_offset_width(g2d, c)
        window.run_command('toggle_side_bar')
        offset2 = self.calc_group_offset_width(g2d, c)
        window.run_command('toggle_side_bar')
        diff = sum(offset2) - sum(offset1)
        width = abs(diff)
        print('side_bar_status: ' + str(offset1))
        # TODO
        # if c > 1:
        #     width += self.get_setting('imesupport_view_frame_right') * (c - 1)
        return {'visible': diff > 0, 'width': width}

    def calc_group_offset_width(self, g2d, group_col):
        r = len(g2d)
        ret = []
        for x in range(group_col):
            for y in range(r):
                if g2d[y][x] is not None:
                    ret += self.calc_view_width(g2d[y][x])
                    break
            else:
                print('WindowLayout.calc_group_offset_width: there is empty view.')
        return ret

    def calc_group_offset_height(self, g2d, group_row):
        c = len(g2d[0])
        ret = []
        for y in range(group_row):
            for x in range(c):
                if g2d[y][x] is not None:
                    ret += self.calc_view_height(g2d[y][x])
                    break
            else:
                print('WindowLayout.calc_group_offset_height: there is empty view.')
        return ret

    def calc_view_width_offset(self, view):
        # TODO get from cache
        line_numbers = WindowLayout.line_numbers_status(view)
        return [
            self.get_setting('imesupport_view_left_icon_width'),
            (line_numbers['width'] if line_numbers['visible'] else 0)
            ]

    def calc_view_width(self, view):
        return self.calc_view_width_offset(view) + [
            view.viewport_extent()[0],
            (self.minimap['width'] if self.minimap['visible'] else 0),
            self.get_setting('imesupport_view_right_vscroll_width')
            ]

    def calc_view_height_offset(self, view):
        return [self.tabs['height'] if self.tabs['visible'] else 0]

    def calc_view_height(self, view):
        # TODO get from cache
        hscroll_bar = WindowLayout.hscroll_bar_status(view)
        return self.calc_view_height_offset(view) + [
            view.viewport_extent()[1],
            (hscroll_bar['height'] if hscroll_bar['visible'] else 0)
            ]

    @staticmethod
    def get_group_list(window):
        return [window.active_view_in_group(g) for g in range(window.num_groups())]

    @staticmethod
    def get_extent_list(window):
        view_groups = [window.active_view_in_group(g) for g in range(window.num_groups())]
        return [None if v is None else v.viewport_extent() for v in view_groups]

    @staticmethod
    def tabs_status(window, view):
        extent1 = view.viewport_extent()
        window.run_command('toggle_tabs')
        extent2 = view.viewport_extent()
        window.run_command('toggle_tabs')
        diff = extent2[1] - extent1[1]
        return {'visible': diff > 0, 'height': abs(diff)}

    @staticmethod
    def is_side_bar_visible(window, view):
        extent1 = view.viewport_extent()
        window.run_command('toggle_side_bar')
        extent2 = view.viewport_extent()
        window.run_command('toggle_side_bar')
        diff = extent2[0] - extent1[0]
        # NOTE Cannot use diff for side_bar width.
        return {'visible': diff > 0}

    @staticmethod
    def minimap_status(window, view):
        extent1 = view.viewport_extent()
        window.run_command('toggle_minimap')
        extent2 = view.viewport_extent()
        window.run_command('toggle_minimap')
        diff = extent2[0] - extent1[0]
        return {'visible': diff > 0, 'width': abs(diff)}

    @staticmethod
    def line_numbers_status(view):
        # XXX Cannot get line number width correctly with non-active group.
        # print(imesupportplugin.WindowLayout.line_numbers_status(window.active_view_in_group(0)))

        visible = view.settings().get('line_numbers')
        # view.settings().set('line_numbers', True)
        # extent1 = view.viewport_extent()
        # view.settings().set('line_numbers', False)
        # extent2 = view.viewport_extent()
        # view.settings().set('line_numbers', visible)
        # diff = extent2[0] - extent1[0]

        char_width = WindowLayout.get_char_width(view) - 1
        width = WindowLayout.calc_line_numbers_width(view, char_width) + 3
        return {'visible': visible, 'width': width}
        # return {'visible': visible, 'width': width, 'diff_width': abs(diff)}

    @staticmethod
    def hscroll_bar_status(view):
        word_wrap = view.settings().get('word_wrap')
        # Make hscroll bar visible if line is longer than viewport.
        view.settings().set('word_wrap', False)
        extent1 = view.viewport_extent()
        # Hide hscroll bar.
        view.settings().set('word_wrap', True)
        extent2 = view.viewport_extent()
        view.settings().set('word_wrap', word_wrap)
        diff = extent2[1] - extent1[1]
        return {'visible': diff > 0, 'height': abs(diff)}

    @staticmethod
    def get_layout_rowcol(layout):
        c = len(layout['cols']) - 1
        r = len(layout['rows']) - 1
        return (r, c)

    @staticmethod
    def get_group_rowcol(layout, group):
        c = len(layout['cols']) - 1
        return (group // c, group % c)

    @staticmethod
    def make_list2d(lst, cols):
        assert (len(lst) % cols) == 0
        return [lst[i * cols:(i + 1) * cols] for i in range(len(lst) / cols)]

    @staticmethod
    def get_char_width(view):
        # Find half width char.
        # FIXME How to handle double width char? Sometimes it cannot import unicodedata.
        r = view.find(r'^[\x20-\x7E]+$', 0)
        if r is None:
            return 8  # Default char width
        text = view.substr(r)
        p1 = view.text_to_layout(r.begin())
        p2 = view.text_to_layout(r.end())
        assert p1[1] == p2[1]
        width = p2[0] - p1[0]
        count = len(text)
        return width / count

    @staticmethod
    def get_number_column(n):
        return int(math.log10(n)) + 1

    @staticmethod
    def calc_line_numbers_width(view, char_width):
        lines, _ = view.rowcol(view.size())
        c = WindowLayout.get_number_column(lines + 1)
        return c * char_width


class _WindowLayoutTestEventListener(sublime_plugin.EventListener):
    def __init__(self):
        window = sublime.active_window()
        if window is None:
            return
        view = window.active_view()
        if view is None:
            return
        self.test(window, view)

    @staticmethod
    def test(window, view):
        print('_WindowLayoutTestEventListener')
        for k, v in WindowLayout(window).get_status().items():
            print(k + ': ' + str(v))


class ImeSupportGetMeasureCommand(sublime_plugin.WindowCommand):
    def run(self):
        _WindowLayoutTestEventListener.test(self.window, self.window.active_view())

# class ImeSupportUpdatePositionCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         view = self.view
#         if view.window() is None:
#             sublime.status_message('IMESupport: view.window() is None')
#             return
#         hwnd = view.window().hwnd()

#         # FIXME not work If the same file is open in multiple tabs.

#         p = calc_position(view)
#         set_inline_position(hwnd, int(p[0]), int(p[1]))
#         # sublime.status_message('ime_inline_update_position')


class ImeInlineEventListener(sublime_plugin.EventListener):
    def __init__(self):
        self.layouts = {}

    def on_activated(self, view):
        self.update(view)

    def on_selection_modified(self, view):
        self.update(view)

    def update(self, view):
        if view is None:
            return
        window = view.window()
        if window is None:
            return

        subclass.setup(view.window().hwnd(), callback)

        id = window.id()
        if id not in self.layouts:
            self.layouts[id] = WindowLayout(window)

        global last_pos
        self.layouts[id].update_status(view)
        last_pos = self.layouts[id].calc_cursor_position(view, view.sel()[0].a)


# class _ImeSupportWindowSetupCommand(sublime_plugin.WindowCommand):
#     def __init__(self, window):
#         subclass.setup(window.hwnd(), callback)

#     def is_enabled(self):
#         return False

#     def is_visible(self):
#         return False
