# for MinGW.

TARGET=../imesupport_hook_x86.dll
SRC=imesupport_hook.c
HEADER=imesupport_hook.h
CFLAGS=-O2 -Wall -shared -m32
LDFLAGS+=-limm32
OPT=

all: $(TARGET)

$(TARGET): $(SRC) $(HEADER)
	gcc $(CFLAGS) $(OPT) -o $(TARGET) $(SRC) $(LDFLAGS)

.PHONY: clean
clean:
	rm -f $(TARGET)
