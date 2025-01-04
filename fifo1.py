# fifo1.py - fifo
#
# stallable synchronous fifo in flops
#
import S
import V
import fifo

P = print

def reinit():
    global params, xx2fifo, fifo2xx

    xx2fifo = { 'dat': 8 }
    fifo2xx = xx2fifo.copy()

    params = { 'd':             3, 
               'w':             V.iface_width( xx2fifo ),
               'wr':            'xx2fifo',
               'rd':            'fifo2xx' }

def inst_fifo1( module_name, inst_name, do_decls=True ):
    params['m_name'] = module_name
    fifo.inst( params, inst_name, 'xx2fifo', 'fifo2xx', xx2fifo, with_wr_prdy=True, do_decl=do_decls )

def make_fifo1( module_name ):
    params['m_name'] = module_name
    fifo.make( params )

def make_tb_fifo1( name, module_name ):
    params['m_name'] = module_name
    fifo.make_tb( name, params, xx2fifo )
