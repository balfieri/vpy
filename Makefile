# This is intended to work on macOS (Darwin), Linux, and Windows. 
# For Linux and Windows, we assume an anaconda3 python3 environment, but that can be changed easily.
# vsim.py currently assumes icarus verilog (iverilog), but that can also be changed easily.
#
# make xxx.v	   -- just makes this one .v file
# make		   -- makes all .v and testbench .v files
# make tb_xxx.out  -- runs tb_xxx.v testbench around design xxx
# make tb_xxx.dout -- ditto, but produces .vcd dump
# make test	   -- runs all testbenches, which should all pass
# make dtest	   -- ditto, but generates .vcd dumps for them all
#
FLAGS=-std=c++17 -O0 -Werror -Wextra -Wstrict-aliasing -pedantic -Wcast-qual -Wctor-dtor-privacy -Wdisabled-optimization -Wformat=2 -Winit-self -Wmissing-include-dirs  -Woverloaded-virtual -Wredundant-decls -Wsign-promo -Wstrict-overflow=5 -Wswitch-default -Wundef -g -lz -lpthread -I../simplert 
FLAGS+=-DASTC_HACK_HDR

OS=$(shell uname)
ifeq ($(OS), Darwin)  	# macOS
CC=clang
GPP=g++
PYTHON3=/usr/local/bin/python3
FLAGS+=-Wno-pragma-pack

else
ifeq ($(OS), Linux)
# assume Linux with anaconda
FLAGS+=-Wno-empty-body -Wno-strict-overflow -Wno-switch-default -Wno-shift-negative-value -Wno-maybe-uninitialized -Wno-sign-promo -Wno-overloaded-virtual -DNO_FMT_LL
GPP=export PATH=/home/utils/gcc-8.1.0/bin:/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib:/etc:/home/nv/bin:/home/utils/p4-2018.1/bin:/usr/local/lsf/bin; g++
PYTHON3=/anaconda/envs/env/bin/python

else
# assume Windows with anaconda3
PYTHON3=C:/anaconda3/python
endif
endif

# example designs
#
MODULES=\
        arb_rr \
	l0c \
	l0c_tags \

#------------------------------------------------------------------------------
# The following rules shouldn't need to change.
#
DEPS=Makefile *.py
TB_MODULES=$(patsubst %,tb_%,$(MODULES))
V_MODULES=$(patsubst %,%.v,$(MODULES))
TB_V_MODULES=$(patsubst %,tb_%,$(V_MODULES))
TEST_OUTS=$(patsubst %,%.out, $(TB_MODULES))
TEST_DOUTS=$(patsubst %,%.dout, $(TB_MODULES))

all: $(V_MODULES) $(TB_V_MODULES)

test: $(TEST_OUTS)

dtest: $(TEST_DOUTS)

tb_%.v: %.v

%.v: $(DEPS)
	$(PYTHON3) gen.py $(patsubst %.v,%, $@) &> $@

%.out: %.v
	$(PYTHON3) vsim.py $(patsubst %.out, %, $@) &> $@

%.dout: %.v
	$(PYTHON3) vsim.py $(patsubst %.dout, %, $@) +dump &> $@

%.vlint: %.v
	verilator --lint-only -Wall $(patsubst %.vlint, %.v, $@)

clean:
	rm -fr *.v *.vvp *.vcd *.lxt *.out *.dout __pycache__ $(TB_MODULES)
