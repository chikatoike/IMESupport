# -*- coding: utf-8 -*-
import ctypes
from ctypes.wintypes import WPARAM, LPARAM, MSG


WH_GETMESSAGE = 3

hook_handle = None
hook_callback = None


def message_hook_func(code, wParam, lParam):
    if hook_callback is not None:
        msg = ctypes.cast(lParam, ctypes.POINTER(MSG))
        hook_callback(msg[0].hWnd, msg[0].message, msg[0].wParam, msg[0].lParam)
    return ctypes.windll.user32.CallNextHookEx(hook_handle, code, wParam, lParam)


prototype = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_long, WPARAM, LPARAM)
proc_obj = prototype(message_hook_func)


def setup(callback):
    global hook_handle
    global hook_callback
    hook_callback = callback

    if hook_handle is not None:
        term()

    hook_handle = ctypes.windll.user32.SetWindowsHookExW(
        WH_GETMESSAGE, proc_obj, 0,
        ctypes.windll.Kernel32.GetCurrentThreadId())


def term():
    global hook_handle
    global hook_callback
    hook_callback = None
    if hook_handle is not None:
        ctypes.windll.user32.UnhookWindowsHookEx(hook_handle)
        hook_handle = None


def test():
    # Required pywin32
    import win32gui
    import win32con
    import time

    def on_create(hwnd):
        def test_callback(hwnd, msg, wParam, lParam):
            if msg == win32con.WM_KEYDOWN:
                print('Subclased OnKeyDown')
                return 0
            return None

        setup(test_callback)

    # Original: http://kb.worldviz.com/articles/791
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

    def CreateWindow(title, message_map, (l, t, r, b)):
        """Create a window with defined title, message map, and rectangle"""
        wc = win32gui.WNDCLASS()
        wc.lpszClassName = 'test_win32gui_1'
        wc.style = win32con.CS_GLOBALCLASS | win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hbrBackground = win32con.COLOR_WINDOW + 1
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.lpfnWndProc = message_map
        win32gui.RegisterClass(wc)
        hwnd = win32gui.CreateWindow(wc.lpszClassName,
            title,
            win32con.WS_CAPTION | win32con.WS_VISIBLE | win32con.WS_SYSMENU,
            l, t, r, b, 0, 0, 0, None)

        on_create(hwnd)

        while win32gui.PumpWaitingMessages() == 0:
            time.sleep(0.01)
        win32gui.UnregisterClass(wc.lpszClassName, None)

    #Display sample window
    CreateWindow('Pywin32 sample', wndproc, (100, 100, 500, 200))


if __name__ == '__main__':
    test()
