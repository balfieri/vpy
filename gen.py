# gen.py - generate one .v modules
#
import sys
import re
import S
import V

# example designs:
import C                        # config file
import l0c                      # L0 cache

if len( sys.argv ) != 4: S.die( 'usage: gen.py module_name op for_test' )

module_name = sys.argv[1]
m           = sys.argv[2]
for_test    = int(sys.argv[3])

C.reinit()

m_lc = m.lower()
builder = None
if S.match( m_lc, '^l0c$' ):            builder = l0c
if not builder: S.die( f'unknown design: {m_lc}' )

builder.reinit()

if for_test:
    make_fn = getattr( builder, f'make_tb_{m_lc}' )
    make_fn( m_lc, module_name )
else:
    make_fn = getattr( builder, f'make_{m_lc}' )
    make_fn( module_name )
