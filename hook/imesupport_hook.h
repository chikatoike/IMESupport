#ifndef _IMESUPPORT_HOOK_H_
#define _IMESUPPORT_HOOK_H_

#include <windows.h>


#define EXPORT

#define WM_IMESUPPORT_SET_INLINE_POSITION 0xB000
#define INVALID_VALUE 0xffffffff


EXPORT BOOL StartHook(void);
EXPORT BOOL EndHook(void);
EXPORT BOOL SetInlinePosition(HWND hWnd, int x, int y, int font_height);

#endif
