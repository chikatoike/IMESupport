import ctypes
from os.path import join, dirname, abspath

WM_IMESUPPORT_SET_INLINE_POSITION = -1
INVALID_VALUE = 0xffff

imesupport_dll = None


def setup(arch_x64, dll_dir=dirname(dirname(abspath(__file__)))):
    # Default DLL location: ../imesupport_hook_xxx.dll
    global imesupport_dll
    global WM_IMESUPPORT_SET_INLINE_POSITION
    if imesupport_dll is not None:
        return True

    imesupport_dll = ctypes.cdll.LoadLibrary(
        join(dll_dir,
            'imesupport_hook_x64.dll' if arch_x64 else
            'imesupport_hook_x86.dll'
            ))
    WM_IMESUPPORT_SET_INLINE_POSITION = imesupport_dll.GetImeSupportMessage()
    return imesupport_dll.StartHook()


def term():
    global imesupport_dll
    if imesupport_dll is not None:
        imesupport_dll.EndHook()
        del imesupport_dll
        imesupport_dll = None


def set_inline_position(hwnd, x, y, font_face, font_height):
    # TODO Use font_face
    if imesupport_dll is not None:
        ctypes.windll.user32.SendMessageW(
            hwnd, WM_IMESUPPORT_SET_INLINE_POSITION, x << 16 | y, font_height)


def clear_inline_position(hwnd):
    if imesupport_dll is not None:
        ctypes.windll.user32.SendMessageW(
            hwnd, WM_IMESUPPORT_SET_INLINE_POSITION, INVALID_VALUE, INVALID_VALUE)


def test():
    # Required pywin32
    import win32gui
    import win32con
    import time

    def on_create(hwnd):
        x = 100
        y = 100
        font_height = 20

        import platform

        setup(platform.machine() == 'AMD64')
        set_inline_position(hwnd, x, y, 'font', font_height)

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

    def CreateWindow(title, message_map, location):
        """Create a window with defined title, message map, and rectangle"""
        l, t, r, b = location
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
    term()


if __name__ == '__main__':
    test()
