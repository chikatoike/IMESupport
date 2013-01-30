#define _CRT_SECURE_NO_WARNINGS

#include <windows.h>
#include <stdio.h>
#include <tchar.h>
#include "imesupport_hook.h"


static LRESULT CALLBACK MyHookProc(int nCode, WPARAM wp, LPARAM lp);
static LRESULT CALLBACK WindowMessageHookProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);
static void Trace2(const TCHAR *str, BOOL append);
static void Trace(const TCHAR *str);


static BOOL bEnableTrace = FALSE;
static HINSTANCE hModule = NULL;
static HHOOK hHook = NULL;


BOOL WINAPI DllMain(HINSTANCE hModuleDLL, DWORD fdwReason, LPVOID lpvReserved)
{
	hModule = hModuleDLL;

	switch (fdwReason) {
	case DLL_PROCESS_ATTACH:
		Trace(_T("DLL_PROCESS_ATTACH"));
		break;
	case DLL_PROCESS_DETACH:
		Trace(_T("DLL_PROCESS_DETACH"));
		if (hHook != NULL) {
			EndHook();
		}
		break;
	}
    return TRUE;
}

EXPORT BOOL StartHook(void)
{
	if (hHook != NULL) {
		return FALSE;
	}
	Trace(_T("start"));
	hHook = SetWindowsHookEx(WH_CALLWNDPROC, MyHookProc, hModule, 0);
	return hHook != NULL;
}

EXPORT BOOL EndHook(void)
{
	Trace(_T("end"));
	return UnhookWindowsHookEx(hHook) != 0;
}

EXPORT BOOL SetInlinePosition(HWND hWnd, int x, int y, int font_height)
{
	BOOL ret = FALSE;
	HIMC hIMC = ImmGetContext(hWnd);

	if (ImmGetOpenStatus(hIMC)) {
		COMPOSITIONFORM cf = {0};
		cf.dwStyle = CFS_POINT;
		cf.ptCurrentPos.x = x;
		cf.ptCurrentPos.y = y;
		if (ImmSetCompositionWindow(hIMC, &cf)) {
			LOGFONT lf = {0};
			lf.lfHeight = font_height;
			// lf.lfFaceName = font_face;
			if (ImmSetCompositionFontW(hIMC, &lf)) {
				ret = TRUE;
			}
		}
	}

	ImmReleaseContext(hWnd, hIMC);
	return ret;
}

static LRESULT CALLBACK MyHookProc(int nCode, WPARAM wp, LPARAM lp)
{
    if (nCode < 0) {
        return CallNextHookEx(hHook, nCode, wp, lp);
    }
    else if (nCode == HC_ACTION) {
        if (wp == 0) {
            const CWPSTRUCT *pcwp = (const CWPSTRUCT *)lp;
            WindowMessageHookProc(pcwp->hwnd, pcwp->message, pcwp->wParam, pcwp->lParam);
        }
    }

    return CallNextHookEx(hHook, nCode, wp, lp);
}

static LRESULT CALLBACK WindowMessageHookProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
	static int x = INVALID_VALUE;
	static int y = INVALID_VALUE;
	static int font_height = INVALID_VALUE;

	switch (msg) {
	case WM_IME_STARTCOMPOSITION:
	case WM_IME_COMPOSITION:
		if (x != INVALID_VALUE && y != INVALID_VALUE && font_height != INVALID_VALUE) {
			Trace(_T("WM_IME_COMPOSITION"));
			SetInlinePosition(hWnd, x, y, font_height);
		}
		break;
	case WM_IMESUPPORT_SET_INLINE_POSITION:
		if (wParam != INVALID_VALUE && lParam != INVALID_VALUE) {
			if (!bEnableTrace) {
				bEnableTrace = TRUE;
				Trace2(_T("start log"), FALSE);
			}
			Trace(_T("WM_IMESUPPORT_SET_INLINE_POSITION"));
			x = (wParam >> 16) & 0xffff;
			y = wParam & 0xffff;
			font_height = lParam;
		}
		else {
			x = INVALID_VALUE;
			y = INVALID_VALUE;
			font_height = INVALID_VALUE;
		}
		break;
	}

	return 0;
}

static void Trace2(const TCHAR *str, BOOL append)
{
#ifdef _DEBUG
	FILE *fp;
	TCHAR szLogFile[_MAX_PATH];
	TCHAR szFull[_MAX_PATH];
	TCHAR szDrive[_MAX_DRIVE];
	TCHAR szDir[_MAX_DIR];

	if (!bEnableTrace) {
		return;
	}

	GetModuleFileName(hModule, szFull, sizeof(szFull) / sizeof(TCHAR));
	_tsplitpath(szFull, szDrive, szDir, NULL, NULL);
	_tmakepath(szLogFile, szDrive, szDir, _T("imesupport"), _T("log"));

	fp = _tfopen(szLogFile, append ? _T("a") : _T("w"));

	if (fp == NULL) {
		return;
	}

	_ftprintf(fp, _T("%s"), str);
	_ftprintf(fp, _T("\n"));
	fclose(fp);
#endif
}

static void Trace(const TCHAR *str)
{
	Trace2(str, TRUE);
}
