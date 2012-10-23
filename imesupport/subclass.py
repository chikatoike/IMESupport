# -*- coding: utf-8 -*-
import ctypes
from ctypes.wintypes import HWND, UINT, WPARAM, LPARAM


prototype = ctypes.WINFUNCTYPE(ctypes.c_long, HWND, UINT, WPARAM, LPARAM)
GWL_WNDPROC = -4

WINPROC = None
_callback_proc = None

subclass_map = {}  # {HWND: {'orig': ORIGINAL_WINPROC, 'callback': CALLBACK}}


def proc_func(hwnd, msg, wParam, lParam):
    if not _callback_proc is None:
        _callback_proc(hwnd, msg, wParam, lParam)
    return ctypes.windll.user32.CallWindowProcW(WINPROC, hwnd, msg, wParam, lParam)


proc_obj = prototype(proc_func)


def setup(hwnd, callback):
    global _callback_proc
    global WINPROC
    _callback_proc = callback

    if WINPROC is None:
        proc = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_WNDPROC)
        if proc != proc_obj:
            WINPROC = proc
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_WNDPROC, proc_obj)


def term(hwnd):
    global WINPROC
    if not WINPROC is None:
        proc = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_WNDPROC)
        if proc == proc_obj:
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_WNDPROC, WINPROC)
            WINPROC = None
        else:
            # Unexpected
            pass
