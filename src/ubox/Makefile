LIB := ../../lib/ubox.lib
all: $(LIB)

AS := sdasz80
AR := sdar

SOURCES := $(wildcard ubox_*.z80)
OBJS := $(patsubst %.z80,%.rel,$(SOURCES))

$(LIB): $(OBJS)
	$(AR) -rcD $(LIB) $(OBJS)

%.rel: %.z80
	$(AS) -o $<

.PHONY: clean
clean:
	rm -f $(OBJS) $(LIB)

