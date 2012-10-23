# -*- coding: utf-8 -*-
import ctypes
from ctypes.wintypes import HWND, UINT, WPARAM, LPARAM


prototype = ctypes.WINFUNCTYPE(ctypes.c_long, HWND, UINT, WPARAM, LPARAM)
GWL_WNDPROC = -4

subclass_map = {}  # {HWND: {'orig': ORIGINAL_WINPROC, 'callback': CALLBACK}}


def proc_func(hwnd, msg, wParam, lParam):
    if hwnd in subclass_map:
        subclass_map[hwnd]['callback'](hwnd, msg, wParam, lParam)
    return ctypes.windll.user32.CallWindowProcW(
        subclass_map[hwnd]['orig'], hwnd, msg, wParam, lParam)


proc_obj = prototype(proc_func)


def setup(hwnd, callback):
    if hwnd not in subclass_map:
        proc = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_WNDPROC)
        if proc != proc_obj:
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_WNDPROC, proc_obj)
            subclass_map[hwnd] = {'orig': proc, 'callback': callback}
        else:
            assert False  # Unexpected
    else:
        subclass_map[hwnd]['callback'] = callback


def term(hwnd):
    if hwnd in subclass_map:
        proc = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_WNDPROC)
        if proc == proc_obj:
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_WNDPROC, subclass_map[hwnd]['orig'])
        else:
            assert False  # Unexpected
        del subclass_map[hwnd]


def test():
    def on_create(hwnd):
        def test_callback(hwnd, msg, wParam, lParam):
            if msg == win32con.WM_KEYDOWN:
                print('Subclased OnKeyDown')

        setup(hwnd, test_callback)
        print('after setup', subclass_map)
        setup(hwnd, test_callback)
        print('after setup', subclass_map)

    # Original: http://kb.worldviz.com/articles/791
    import win32gui, win32con
    import time

    def OnKeyDown(hwnd, msg, wp, lp):
        print('Original OnKeyDown')

    def OnClose(hwnd, msg, wparam, lparam):
        """Destroy window when it is closed by user"""
        win32gui.DestroyWindow(hwnd)

    def OnDestroy(hwnd, msg, wparam, lparam):
        """Quit application when window is destroyed"""
        win32gui.PostQuitMessage(0)

    #Define message map for window
    wndproc = {
            win32con.WM_KEYDOWN: OnKeyDown,
            win32con.WM_CLOSE: OnClose,
            win32con.WM_DESTROY: OnDestroy
            }

    def CreateWindow(title,message_map,(l,t,r,b)):
        """Create a window with defined title, message map, and rectangle"""
        wc = win32gui.WNDCLASS()
        wc.lpszClassName = 'test_win32gui_1'
        wc.style =  win32con.CS_GLOBALCLASS|win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hbrBackground = win32con.COLOR_WINDOW+1
        wc.hCursor = win32gui.LoadCursor( 0, win32con.IDC_ARROW )
        wc.lpfnWndProc = message_map
        class_atom = win32gui.RegisterClass(wc)
        hwnd = win32gui.CreateWindow(wc.lpszClassName,
            title,
            win32con.WS_CAPTION|win32con.WS_VISIBLE|win32con.WS_SYSMENU,
            l,t,r,b, 0, 0, 0, None)

        on_create(hwnd)

        while win32gui.PumpWaitingMessages() == 0:
            time.sleep(0.01)
        win32gui.UnregisterClass(wc.lpszClassName, None)

    #Display sample window
    CreateWindow('Pywin32 sample',wndproc,(100,100,500,200))


if __name__ == '__main__':
    test()
