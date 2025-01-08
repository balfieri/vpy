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
# fifo1.py - stallable synchronous fifo in flops
#
import S
import V
import fifo

P = print

def reinit():
    global params, xx2fifo, fifo2xx

    # normally, this stuff would go in a C.py config file
    xx2fifo = { 'dat': 8 }
    fifo2xx = xx2fifo.copy()

    params = { 'd':             3, 
               'w':             V.iface_width( xx2fifo ),
               'wr':            'xx2fifo',
               'rd':            'fifo2xx' }

def inst_fifo1( module_name, inst_name, do_decls=True ):
    fifo.inst( params, module_name, inst_name, 'xx2fifo', 'fifo2xx', xx2fifo, with_wr_prdy=True, do_decl=do_decls )

def make_fifo1( module_name ):
    fifo.make( params, module_name )

def make_tb_fifo1( module_name, inst_name ):
    fifo.make_tb( params, module_name, inst_name, xx2fifo )
