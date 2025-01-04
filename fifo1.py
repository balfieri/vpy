# fifo1.py - fifo
#
# stallable synchronous fifo in flops
#
import S
import V
import C
import math

P = print

def reinit():
    global params, xx2fifo, fifo2xx

    params = { 'depth':          3, 
               'w':              8,
               'is_async':       False, 
               'wr_clk':         V.clk,
               'wr_reset_':      V.reset_,
               'wr':             'xx2fifo',
               'rd_clk':         V.clk,
               'rd_reset_':      V.reset_,
               'rd':             'fifo2xx' }

    xx2fifo                   = { 'dat': params['w'] }
    fifo2xx                   = xx2fifo.copy()

# this is here for completeness, but is not used by anything
def inst_fifo1( module_name, inst_name, do_decls=True ):
    params['m_name'] = module_name
    V.inst_fifo( params, inst_name, 'xx2fifo', 'fifo2xx', xx2fifo, 'pvld', 'prdy', with_wr_prdy=True, do_decl=do_decls )

def make_fifo1( module_name ):
    params['m_name'] = module_name
    V.make_fifo( params )  # non-standard way that explicitly makes this module as a fifo module

def make_tb_fifo1( name, module_name ):
    params['m_name'] = module_name
    V.make_fifo_tb( name, params, xx2fifo )
