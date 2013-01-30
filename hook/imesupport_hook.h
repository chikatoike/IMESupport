#ifndef _IMESUPPORT_HOOK_H_
#define _IMESUPPORT_HOOK_H_

#include <windows.h>


#ifdef _MSC_VER
  #define EXPORT __declspec(dllexport)
#else
  #define EXPORT
#endif

#define INVALID_VALUE 0xffffffff


EXPORT BOOL StartHook(void);
EXPORT BOOL EndHook(void);
EXPORT int GetMessageId(void);
EXPORT BOOL SetInlinePosition(HWND hWnd, int x, int y, int font_height);

#endif
