all: ..\imesupport_hook_x86.dll

..\imesupport_hook_x86.dll: imesupport_hook_x86.dll
	copy imesupport_hook_x86.dll ..\imesupport_hook_x86.dll

imesupport_hook_x86.dll: imesupport_hook.c
	cl /wd4996 /LD /Feimesupport_hook_x86.dll imesupport_hook.c imm32.lib user32.lib

clean:
	cmd /C "del ..\imesupport_hook_x86.dll imesupport_hook_x86.dll imesupport_hook_x86.exp imesupport_hook_x86.lib imesupport_hook.obj" /F /Q
