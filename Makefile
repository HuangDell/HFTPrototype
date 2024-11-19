# binary name  
APP = Prototype  

# all source are stored in SRCS-y  
SRCS-y := $(wildcard src/*.c)  
PKGCONF ?= pkg-config  

# Build using pkg-config variables if possible  
ifneq ($(shell $(PKGCONF) --exists libdpdk && echo 0),0)  
$(error "no installation of DPDK found")  
endif  

# Base CFLAGS  
CFLAGS_BASE := $(shell $(PKGCONF) --cflags libdpdk)  
CFLAGS_BASE += -I./include  
CFLAGS_BASE += -DALLOW_EXPERIMENTAL_API  

# Debug flags  
CFLAGS_DEBUG := $(CFLAGS_BASE) -g -O0 -DDEBUG  
# Release flags  
CFLAGS_RELEASE := $(CFLAGS_BASE) -O3  

# Default to release flags  
CFLAGS := $(CFLAGS_RELEASE)  

PC_FILE := $(shell $(PKGCONF) --path libdpdk 2>/dev/null)  
LDFLAGS += $(shell $(PKGCONF) --libs libdpdk)  

all: build/$(APP)  
.PHONY: all debug clean  

debug: CFLAGS := $(CFLAGS_DEBUG)  
debug: build/$(APP)  

build/$(APP): $(SRCS-y) Makefile $(PC_FILE) | build  
	$(CC) $(CFLAGS) $(SRCS-y) -o $@ $(LDFLAGS)  

build:  
	@mkdir -p $@  

clean:  
	rm -f build/$(APP)  
	test -d build && rmdir -p build || true