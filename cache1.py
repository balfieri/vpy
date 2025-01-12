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
# cache1.py - simple L0 cache all in flops
#
import S
import V
import cache

P = print

def reinit():
    global params;

    # I am confused about subword cnt from C.py
    params = { # required:
               'line_cnt':      2,              # number of lines
               'assoc':         2,              # fully associative (one set)
               'line_w':        32,             # width of line (dat)
               'req_id_w':      3,              # width of req_id in request
               'req_addr_w':    30,             # width of virtual address in request

               # optional:
               'is_read_only':  True,           # read-only cache
               'cache_name':    'l0c',          # short name used in interfaces
               'unit_name':     'xx',           # short name used in interfaces
               'mem_name':      'mem',          # short name used in interfaces
               'ref_cnt_max':   2,              # max reference count per line
               'tag_ram_kind':  'ff',           # tag ram in flops
               'data_ram_kind': 'ff',           # data ram in flops
               'req_cnt':       1,              # number of request interfaces
               'mem_dat_w':     64,             # memory width
             }

def inst_cache1( module_name, inst_name, do_decls ):
    cache.inst( params, module_name, inst_name, do_decls=do_decls )

def make_cache1( module_name ):
    cache.make( params, module_name );

def make_tb_cache1( module_name, inst_name ):
    cache.make_tb( params, module_name, inst_name )
