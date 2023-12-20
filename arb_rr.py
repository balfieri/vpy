# arb_rr.py - round-robin arbiter
#
# simple round-robin arbiter
#
import S
import V
import C
import math

P = print

def reinit():
    pass

def header( module_name ):
    P(f'// Round-robin arbiter with the following properties:' )
    P(f'// - combinational eligible mask input' )
    P(f'// - combinational chosen_id output' )
    P(f'// - round-robin fairness' )
    P(f'//' )
    V.module_header_begin( module_name )
    V.input( f'{V.clk}', 1 )
    V.input( f'{V.reset_}', 1 )
    V.output( f'arb_idle', 1 )
    V.iface_input( f'xx2arb', C.xx2arb, False )
    V.iface_output( f'arb2xx', C.arb2xx, False )
    V.module_header_end()
    V.iface_dprint( f'xx2arb',               C.xx2arb,               f'xx2arb_pvld' )
    V.iface_dprint( f'arb2xx',               C.arb2xx,               f'arb2xx_pvld' )
  
def inst_arb_rr( module_name, inst_name, do_decls ):
    if do_decls: 
        V.wire( f'arb_idle', 1 )
        V.iface_wire( f'xx2arb', C.xx2arb, True, False )
        V.iface_wire( f'arb2xx', C.arb2xx, True, False )
    P()
    P(f'{module_name} {inst_name}(' ) 
    P(f'      .{V.clk}({V.clk}), .{V.reset_}({V.reset_}), .arb_idle(arb_idle)' )
    V.iface_inst( f'xx2arb', f'xx2arb', C.xx2arb, True, False )
    V.iface_inst( f'arb2xx', f'arb2xx', C.arb2xx, True, False )
    P(f'    );' )

def make_arb_rr( module_name ):
    header( module_name )

    P()
    P( f'// ARBITER' )
    P( f'//' )
    V.choose_eligible( 'req_id_chosen', f'xx2arb_elig', C.arb_req_id_cnt, f'req_preferred', gen_preferred=True, adv_preferred='xx2arb_pvld' )
    P( f'assign arb2xx_pvld = xx2arb_pvld;' )
    P( f'assign arb2xx_req_id = req_id_chosen;' )

    idle = '!xx2arb_pvld && !arb2xx_pvld'
    P( f'assign arb_idle = {idle};' )

    V.module_footer( module_name )

def make_tb_arb_rr( name, module_name ):
    P(f'// Testbench for {module_name}.v with the following properties beyond those of the arbiter:' )
    P(f'// - issues a plusarg-selectable number of requests (default: 100)' )
    P(f'// - randomly chooses the eligibility mask' )
    P(f'// - randomly adds bubbles in the request stream' )
    P(f'// - asserts that the same req_id is not chosen if it was chosen last time and different requestors are eligible this time' )
    P(f'//' )
    V.module_header_begin( f'tb_{module_name}' )
    V.module_header_end()
    P()
    V.tb_clk()
    V.tb_reset_()
    V.tb_dump( f'tb_{module_name}', include_saif=False )
    P()
    V.tb_rand_init()

    inst_arb_rr( module_name, f'u_{name}', True )

    P() 
    P( f'// PLUSARGS' )
    P( f'//' )
    P( f'reg [31:0] req_cnt_max;' )
    P( f'initial begin' )
    P( f'    if ( !$value$plusargs( "req_cnt_max=%d", req_cnt_max ) ) req_cnt_max = 100;' )
    P( f'end' )

    P() 
    P( f'// REQUESTS' )
    P( f'//' )
    V.reg( 'req_cnt', 32 )
    V.tb_randbits( 'can_issue_req', 1 )
    V.tb_randbits( 'elig', C.arb_req_id_cnt )
    P( f'assign xx2arb_pvld = can_issue_req && |elig && req_cnt < req_cnt_max;' )
    P( f'assign xx2arb_elig = elig;' )
    V.reg( 'last_pvld', 1 )
    V.reg( 'last_req_id', C.arb_req_id_w )
    V.always_at_posedge()
    P( f'    if ( !{V.reset_} ) begin' )
    P( f'        req_cnt <= 0;' )
    P( f'        last_pvld <= 0;' )
    P( f'    end else begin' )
    P( f'        if ( xx2arb_pvld ) begin' )
    P( f'            req_cnt <= req_cnt + 1;' )
    P( f'        end' )
    P( f'        if ( arb2xx_pvld ) begin' )
    P( f'            last_pvld <= 1;' )
    P( f'            last_req_id <= arb2xx_req_id;' )
    P( f'        end' )
    P( f'        if ( arb_idle && req_cnt === req_cnt_max ) begin' )
    P( f'            $display( "PASS" );' )
    P( f'            $finish;' )
    P( f'        end' )
    P( f'    end' )
    P( f'end' )
    V.dassert( 'arb_idle === !xx2arb_pvld', 'idle iff iface idle' )
    V.dassert( 'xx2arb_pvld === arb2xx_pvld', 'interfaces should be in sync' )
    V.binary_to_one_hot( 'arb2xx_req_id', C.arb_req_id_cnt, 'chosen_mask', f'({V.reset_} && arb2xx_pvld)' )
    V.dassert( 'arb2xx_pvld === 0 || (xx2arb_elig & chosen_mask) !== 0', f'req chosen that was not eligible' )
    V.binary_to_one_hot( f'last_req_id', C.arb_req_id_cnt, 'last_mask', f'({V.reset_} && last_pvld)' )
    V.dassert( 'arb2xx_pvld === 0 || xx2arb_elig === chosen_mask || chosen_mask !== last_mask', f'arbiter did not choose fairly' )

    P()
    P(f'endmodule // tb_{module_name}' )
