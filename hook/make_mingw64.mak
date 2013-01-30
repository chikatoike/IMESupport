# for MinGW.

TARGET=../imesupport_hook_x64.dll
SRC=imesupport_hook.c
HEADER=imesupport_hook.h
CFLAGS=-O2 -Wall -shared -m64
LDFLAGS+=-limm32
OPT=

all: $(TARGET)

$(TARGET): $(SRC) $(HEADER)
	gcc $(CFLAGS) $(OPT) -o $(TARGET) $(SRC) $(LDFLAGS)

.PHONY: clean
clean:
	rm -f $(TARGET)
