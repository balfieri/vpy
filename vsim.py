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
