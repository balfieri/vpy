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
    global info, xx2fifo, fifo2xx

    info = { 'depth':          3, 
             'w':              8,
             'is_async':       False, 
             'wr_clk':         V.clk,
             'wr_reset_':      V.reset_,
             'wr':             'xx2fifo',
             'rd_clk':         V.clk,
             'rd_reset_':      V.reset_,
             'rd':             'fifo2xx' }

    xx2fifo                   = { 'dat': info['w'] }
    fifo2xx                   = xx2fifo.copy()

# this is here for completeness, but is not used by anything
def inst_fifo1( module_name, inst_name, do_decls=True ):
    info['m_name'] = module_name
    V.inst_fifo( info, inst_name, 'xx2fifo', 'fifo2xx', xx2fifo, 'pvld', 'prdy', with_wr_prdy=True, do_decl=do_decls )

def make_fifo1( module_name ):
    info['m_name'] = module_name
    V.make_fifo( info )  # non-standard way that explicitly makes this module as a fifo module

def make_tb_fifo1( name, module_name ):
    info['m_name'] = module_name
    V.tb_fifo( name, info, xx2fifo )
