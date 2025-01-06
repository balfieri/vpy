# Copyright (c) 2017-2025 Robert A. Alfieri
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# 
# vsim.py - run simple verilog simulation
#
# vsim.py <top_name> [options]
#
# Parses the top_name.v design and creates some number of <top_name>.rand<n> directories with potentially modified 
# copies of the design. Then simulates the design with some random seed and creates a .json file in each directory
# for use in subsequent NN training.
#
import sys
import os
import S

if len( sys.argv ) < 2: S.die( 'vsim <dut> [options] [plusargs]' )

dut = sys.argv[1]
dumper = 'vcd'
do_build = 1
do_run = 1
plusargs = ''
i = 2
while i < len( sys.argv ):
    arg = sys.argv[i]
    i += 1
    if arg[0] == '+':
        print( arg )
        plusargs += f' {arg}' 
        continue
    if arg == '-dumper':
        dumper = sys.argv[i]
    elif arg == '-do_build':
        do_build = int( sys.argv[i] )
    elif arg == '-do_run':
        do_run = int( sys.argv[i] )
    else:
        S.die( f'vsim: unknown option: {arg}' )
    i += 1

defines = '-D __VCD=1' if dumper == 'vcd' else ''
os.environ['IVERILOG_DUMPER'] = dumper
if do_build: S.cmd( f'iverilog -g2012 -Wall {defines} -y. -o {dut}.vvp -s {dut} {dut}.v', echo_stdout=True )
if do_run:   S.cmd( f'vvp ./{dut}.vvp{plusargs}', echo_stdout=True )
