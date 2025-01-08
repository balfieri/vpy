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
# gen.py - generate one .v modules
#
import sys
import re
import S
import V

# example designs:
import C                        # config file
import arb_rr                   # round-robin arbiter
import fifo1                    # stallable fifo in flops
import cache1                   # simple L0 cache in flops

if len( sys.argv ) != 2: S.die( 'usage: gen.py module_name' )

module_name = sys.argv[1]
m           = S.subst( module_name, r'^tb_', '' )
for_test    = module_name != m

C.reinit()

m_lc = m.lower()
builder = None
if m_lc == 'arb_rr':                    builder = arb_rr
if m_lc == 'fifo1':                     builder = fifo1
if m_lc == 'cache1':                    builder = cache1
if not builder: S.die( f'unknown design: {m_lc}' )

builder.reinit()

if for_test:
    make_fn = getattr( builder, f'make_tb_{m_lc}' )
    make_fn( m_lc, m_lc )
else:
    make_fn = getattr( builder, f'make_{m_lc}' )
    make_fn( module_name )
