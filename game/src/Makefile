TARGET := game

CODE := 0x4000
# leaves 222 bytes for AKM player buffer
DATA := 0xc0de

# HEX, will fill with 0
ROM_MAX := 8000

OUTPUT := ../build
OBJS := $(patsubst %.c,$(OUTPUT)/%.rel,$(wildcard *.c)) $(OUTPUT)/akm.rel
UBOX_LIBS := $(wildcard ../../lib/*.lib)
LIBS := -lubox -lspman -lmplayer -lap

CC := sdcc
AS := sdasz80
AR := sdcclib
CFLAGS := -mz80 --Werror -I../../include -I../generated --fsigned-char --std-sdcc99 --opt-code-speed
LDFLAGS := -L../../lib -L. --no-std-crt0 --fomit-frame-pointer

all: $(OUTPUT)/$(TARGET).rom
	@../../tools/chksize 8000 4000 $(OUTPUT)/$(TARGET).map
	@cp ../bin/$(TARGET).rom ../../bin

openmsx: all
	openmsx -carta $(OUTPUT)/$(TARGET).rom -machine msx1

$(OUTPUT)/%.rel: %.c
	$(CC) $(CFLAGS) $(LDFLAGS) -c $< -o $@

$(OUTPUT)/%.rel: %.z80
	$(AS) -g -o $@ $<

$(OUTPUT)/akm.rel: akm.z80 song.asm effects.asm
	rasm akm.z80 -o $(OUTPUT)/akm -s -sl -sq
	Disark --sourceProfile sdcc --symbolFile $(OUTPUT)/akm.sym --src16bitsValuesInHex --src8bitsValuesInHex --undocumentedOpcodesToBytes $(OUTPUT)/akm.bin $(OUTPUT)/akm_sdcc.asm
	$(AS) -g -o $@ $(OUTPUT)/akm_sdcc.asm

$(OUTPUT)/$(TARGET).rom: $(OBJS) $(OUTPUT)/crt0.rel $(UBOX_LIBS)
	$(CC) $(CFLAGS) $(LDFLAGS) $(LIBS) --code-loc $(CODE) --data-loc $(DATA) $(OUTPUT)/crt0.rel $(OBJS) -o $(OUTPUT)/$(TARGET).ihx
	../../bin/hex2bin -e bin -p 00 -l $(ROM_MAX) $(OUTPUT)/$(TARGET).ihx
	@cp $(OUTPUT)/$(TARGET).bin ../bin/$(TARGET).rom

clean:
	rm -f $(OUTPUT)/*
	rm -f ../bin/$(TARGET).rom ../../bin/$(TARGET).rom

.PHONY: all clean

include Makefile.deps
