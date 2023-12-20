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
import l0c                      # L0 cache
import l0c_tags                 # L0 cache tags only

if len( sys.argv ) != 2: S.die( 'usage: gen.py module_name' )

module_name = sys.argv[1]
m           = S.subst( module_name, r'^tb_', '' )
for_test    = module_name != m

C.reinit()

m_lc = m.lower()
builder = None
if m_lc == 'arb_rr':                    builder = arb_rr
if m_lc == 'fifo1':                     builder = fifo1
if m_lc == 'l0c':                       builder = l0c
if m_lc == 'l0c_tags':                  builder = l0c_tags
if not builder: S.die( f'unknown design: {m_lc}' )

builder.reinit()

if for_test:
    make_fn = getattr( builder, f'make_tb_{m_lc}' )
    make_fn( m_lc, m_lc )
else:
    make_fn = getattr( builder, f'make_{m_lc}' )
    make_fn( module_name )
