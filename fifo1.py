# fifo1.py - fifo
#
# stallable fifo in flops
#
import S
import V
import C
import math

P = print

def reinit():
    pass

def header( module_name ):
    P(f'// FIFO with the following properties:' )
    P(f'// - ram built out of flops' )
    P(f'// - depth of {C.fifo_d} entries' )
    P(f'// - width of {C.fifo_w} bits' )
    P(f'// - stallable' )
    P(f'//' )
    V.module_header_begin( module_name )
    V.input( f'{V.clk}', 1 )
    V.input( f'{V.reset_}', 1 )
    V.output( f'fifo_idle', 1 )
    V.iface_input( f'xx2fifo', C.xx2fifo, True )
    V.iface_output( f'fifo2xx', C.fifo2xx, True )
    V.module_header_end()
    V.iface_dprint( f'xx2fifo',               C.xx2fifo,               f'{V.reset_} && xx2fifo_pvld && xx2fifo_prdy' )
    V.iface_dprint( f'fifo2xx',               C.fifo2xx,               f'{V.reset_} && fifo2xx_pvld && fifo2xx_prdy' )
  
def inst_fifo1( module_name, inst_name, do_decls ):
    if do_decls: 
        V.wire( f'fifo_idle', 1 )
        V.iface_wire( f'xx2fifo', C.xx2fifo, True, True )
        V.iface_wire( f'fifo2xx', C.fifo2xx, True, True )
    P()
    P(f'{module_name} {inst_name}(' ) 
    P(f'      .{V.clk}({V.clk}), .{V.reset_}({V.reset_}), .fifo_idle(fifo_idle)' )
    V.iface_inst( f'xx2fifo', f'xx2fifo', C.xx2fifo, True, True )
    V.iface_inst( f'fifo2xx', f'fifo2xx', C.fifo2xx, True, True )
    P(f'    );' )

def make_fifo1( module_name ):
    header( module_name )

    P()
    V.fifo( 'xx2fifo', 'fifo2xx', C.xx2fifo, 'pvld', 'prdy', C.fifo_d, m_name='', u_name='', with_wr_prdy=True )

    idle = '!xx2fifo_pvld && !fifo2xx_pvld'
    P( f'assign fifo_idle = {idle};' )

    V.module_footer( module_name )

def make_tb_fifo1( name, module_name ):
    P(f'// Testbench for {module_name}.v with the following properties beyond those of the fifo:' )
    P(f'// - incrementing input data' )
    P(f'// - randomly adds bubbles to write-side input' )
    P(f'// - randomly stalls the read-side output' )
    P(f'//' )
    V.module_header_begin( f'tb_{module_name}' )
    V.module_header_end()
    P()
    V.tb_clk()
    V.tb_reset_()
    V.tb_dump( f'tb_{module_name}', include_saif=False )
    P()
    V.tb_rand_init()

    inst_fifo1( module_name, f'u_{name}', True )

    P() 
    P( f'// PLUSARGS' )
    P( f'//' )
    P( f'reg [31:0] wr_cnt_max;' )
    P( f'initial begin' )
    P( f'    if ( !$value$plusargs( "wr_cnt_max=%d", wr_cnt_max ) ) wr_cnt_max = 100;' )
    P( f'end' )

    P() 
    P( f'// REQUESTS' )
    P( f'//' )
    V.reg( 'wr_cnt', 32 )
    V.reg( 'rd_cnt', 32 )
    V.tb_randbits( 'can_wr', 1 )
    V.tb_randbits( 'can_rd', 1 )
    V.reg( f'wr_dat', C.fifo_w )
    V.reg( f'rd_dat', C.fifo_w ) # expected
    P( f'assign xx2fifo_pvld = can_wr && wr_cnt < wr_cnt_max;' )
    P( f'assign xx2fifo_dat  = wr_dat;' )
    P( f'assign fifo2xx_prdy = can_rd;' )
    V.always_at_posedge()
    P( f'    if ( !{V.reset_} ) begin' )
    P( f'        wr_cnt <= 0;' )
    P( f'        rd_cnt <= 0;' )
    P( f'        wr_dat <= 0;' )
    P( f'        rd_dat <= 0;' )
    P( f'    end else begin' )
    P( f'        if ( xx2fifo_pvld && xx2fifo_prdy ) begin' )
    P( f'            wr_dat <= wr_dat + 1;' )
    P( f'            wr_cnt <= wr_cnt + 1;' )
    P( f'        end' )
    P( f'        if ( fifo2xx_pvld && fifo2xx_prdy ) begin' )
    P( f'            rd_dat <= rd_dat + 1;' )
    P( f'            rd_cnt <= rd_cnt + 1;' )
    P( f'        end' )
    P( f'        if ( fifo_idle && rd_cnt === wr_cnt_max ) begin' )
    P( f'            $display( "PASS" );' )
    P( f'            $finish;' )
    P( f'        end' )
    P( f'    end' )
    P( f'end' )
    V.dassert( f'fifo2xx_pvld === 0 || fifo2xx_dat === rd_dat', f'unexpected read data' )

    P()
    P(f'endmodule // tb_{module_name}' )
