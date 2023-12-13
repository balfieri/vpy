# l0c_tags.py - L0 Cache Tags Only
#
# Simple L0 Cache - tags only, all in flops
#
import S
import V
import C
import math

P = print

def reinit():
    pass

def header( module_name ):
    P(f'// L0 read-only cache tags only with the following properties:' )
    P(f'// - tags kept in flops' )
    P(f'// - fully-associative' )
    P(f'// - {C.l0c_slot_cnt} lines' )
    P(f'// - {C.addr_w}-bit request byte address, but this is shorted according to the request word width ' )
    P(f'// - each request has an associated {C.l0c_req_id_w}-bit req_id to help the requestor identify the return information' )
    P(f'// - requests are non-blocking, and a req status return interface indicates is_hit, is_miss, and must_retry' )
    P(f'// - must_retry=1 means the cache cannot currently allocate a line OR a hit-under-miss situation' )
    P(f'// - any must_retry request must be retried by the requestor, obviously' )
    P(f'// - maximum per-line reference count of {C.l0c_ref_cnt_max}' )
    P(f'//' )
    V.module_header_begin( module_name )
    V.input( f'{V.clk}', 1 )
    V.input( f'{V.reset_}', 1 )
    V.output( f'l0c_idle', 1 )
    V.iface_input( f'xx2l0c', C.xx2l0c, True )
    V.iface_output( f'l0c2xx_status', C.l0c2xx_status, False )
    V.module_header_end()
    V.wire( f'xx2l0c_d_prdy', 1 )
    V.iface_stage( f'xx2l0c', f'xx2l0c_d', C.xx2l0c, 'pvld', 'prdy', full_handshake=True, do_dprint=False )
    P()
    V.iface_dprint( f'l0c2xx_status', C.l0c2xx_status, f'l0c2xx_status_pvld' )
  
def inst_l0c_tags( module_name, inst_name, do_decls ):
    if do_decls: 
        V.wire( f'l0c_idle', 1 )
        V.iface_wire( f'xx2l0c', C.xx2l0c, True, True )
        V.iface_wire( f'l0c2xx_status', C.l0c2xx_status, True, False )
    P()
    P(f'{module_name} {inst_name}(' ) 
    P(f'      .{V.clk}({V.clk}), .{V.reset_}({V.reset_}), .l0c_idle(l0c_idle)' )
    V.iface_inst( f'xx2l0c', f'xx2l0c', C.xx2l0c, True, True )
    V.iface_inst( f'l0c2xx_status', f'l0c2xx_status', C.l0c2xx_status, True, False )
    P(f'    );' )

def make_l0c_tags( module_name ):
    header( module_name )

    P()
    P( f'// TAGS INPUTS' )
    P( f'//' )
    P( f'assign xx2l0c_d_prdy = 1;' )
    V.wirea( f'tags_req0_pvld', 1, f'xx2l0c_d_pvld && xx2l0c_d_prdy' )
    V.wirea( f'tags_req0_addr', C.l0c_addr_w, f'xx2l0c_d_addr' )
    V.wire( f'tags_decr0_pvld', 1 )
    V.wire( f'tags_decr0_tag_i', C.l0c_slot_id_w )
    V.wire( f'tags_fill_pvld', 1 )
    V.wire( f'tags_fill_tag_i', C.l0c_slot_id_w )

    V.cache_tags( f'tags', C.l0c_addr_w, C.l0c_slot_cnt, 1, C.l0c_ref_cnt_max )

    P()
    P( f'// TAGS STATUS' )
    P( f'//' )
    V.iface_reg( f'l0c2xx_status', C.l0c2xx_status, True, False )
    V.always_at_posedge()
    P( f'    l0c2xx_status_pvld <= tags_req0_pvld;' )
    P( f'    if ( tags_req0_pvld ) begin' )
    P( f'        l0c2xx_status_req_id <= xx2l0c_d_req_id;' )
    P( f'        l0c2xx_status_is_hit <= tags_req0_status == TAGS_HIT;' )
    P( f'        l0c2xx_status_is_miss <= tags_req0_status == TAGS_MISS;' )
    P( f'        l0c2xx_status_must_retry <= tags_req0_status == TAGS_HIT_BEING_FILLED || tags_req0_status == TAGS_MISS_CANT_ALLOC;' )
    P( f'    end' )
    P( f'end' )

    P()
    P( f'// IDLE' )
    P( f'//' )
    idle = '!xx2l0c_d_pvld && tags_idle'
    P( f'assign l0c_idle = {idle};' )

    V.module_footer( module_name )

def make_tb_l0c_tags( name, module_name ):
    P(f'// Testbench for {module_name}.v with the following properties beyond those of the cache:' )
    P(f'// - issues a plusarg-selectable number of requests (default: 100)' )
    P(f'// - randomly selects an address from {C.l0c_tb_addr_cnt} possible random addresses (to induce hits)' )
    P(f'// - randomly adds bubbles in the request stream' )
    P(f'// - randomly decrements the ref cnt in lines' )
    P(f'//' )
    V.module_header_begin( f'tb_{module_name}' )
    V.module_header_end()
    P()
    V.tb_clk()
    V.tb_reset_()
    V.tb_dump( f'tb_{module_name}', include_saif=False )
    P()
    V.tb_rand_init()

    inst_l0c_tags( module_name, f'u_{name}', True )

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
    V.reg( 'req_in_use_mask', C.l0c_req_id_cnt )
    V.reg( 'req_got_status_mask', C.l0c_req_id_cnt )
    addrs = []
    dats_expected = []
    for i in range(C.l0c_tb_addr_cnt):
        addr = S.rand_bits( C.l0c_addr_w )
        V.wirea( f'addr{i}', C.l0c_addr_w, f'{C.l0c_addr_w}\'h{addr:01x}' )
        V.wirea( f'dat_expected{i}', C.l0c_dat_w, f'{C.l0c_dat_w}\'h{addr:01x}' )
        addrs.append( f'addr{i}' )
        dats_expected.append( f'dat_expected{i}' )
    req_addr_is = []
    for i in range(C.l0c_req_id_cnt):
        V.reg( f'req{i}_addr_i', C.l0c_tb_addr_id_w )
        req_addr_is.append( f'req{i}_addr_i' )
    P()
    V.iface_reg( f'xx2l0c_p', C.xx2l0c, True, False )
    P( f'wire   xx2l0c_p_prdy = xx2l0c_prdy;' )
    P( f'assign xx2l0c_pvld = xx2l0c_p_pvld;' )
    P( f'assign xx2l0c_req_id = xx2l0c_p_req_id;' )
    P( f'assign xx2l0c_addr = xx2l0c_p_addr;' )
    V.reg( 'req_cnt', 32 )
    V.wirea( 'req_elig', C.l0c_req_id_cnt, f'~req_in_use_mask' )
    V.tb_randbits( 'should_delay_req_rand', 2 )
    V.wirea( 'should_delay_req', 1, f'should_delay_req_rand == 0' )
    V.wirea( 'can_issue_req', 1, f'req_cnt < req_cnt_max && !should_delay_req && (!xx2l0c_p_pvld || xx2l0c_p_prdy)' )
    V.choose_eligible( 'req_id_chosen', f'req_elig', C.l0c_req_id_cnt, f'req_preferred', gen_preferred=True, adv_preferred='can_issue_req' )
    P( f'// {V.vlint_off_width}' )
    V.binary_to_one_hot( 'req_id_chosen',        C.l0c_req_id_cnt, 'req_issued_mask',            f'({V.reset_} && can_issue_req && req_elig_any_vld)' )
    V.binary_to_one_hot( 'l0c2xx_status_req_id', C.l0c_req_id_cnt, 'req_status_mask',            f'l0c2xx_status_pvld' )
    V.binary_to_one_hot( 'l0c2xx_status_req_id', C.l0c_req_id_cnt, 'req_status_is_hit_mask',     f'l0c2xx_status_pvld && l0c2xx_status_is_hit' )
    V.binary_to_one_hot( 'l0c2xx_status_req_id', C.l0c_req_id_cnt, 'req_status_is_miss_mask',    f'l0c2xx_status_pvld && l0c2xx_status_is_miss' )
    V.binary_to_one_hot( 'l0c2xx_status_req_id', C.l0c_req_id_cnt, 'req_status_must_retry_mask', f'l0c2xx_status_pvld && l0c2xx_status_must_retry' )
    P( f'// {V.vlint_on_width}' )
    V.tb_randbits( 'req_addr_i', C.l0c_tb_addr_id_w )
    V.muxa( 'req_addr', C.l0c_addr_w, 'req_addr_i', addrs )
    P()
    V.always_at_posedge();
    P( f'    if ( !{V.reset_} ) begin' )
    P( f'        req_in_use_mask <= 0;' )
    P( f'        xx2l0c_p_pvld <= 0;' )
    P( f'        req_cnt <= 0;' )
    P( f'    end else begin' )
    P( f'        if ( can_issue_req && req_elig_any_vld ) begin' )
    P( f'            xx2l0c_p_pvld <= 1;' )
    P( f'            xx2l0c_p_req_id <= req_id_chosen;' )
    P( f'            xx2l0c_p_addr <= req_addr;' )
    P( f'            req_cnt <= req_cnt + 1;' )
    for i in range(C.l0c_req_id_cnt):
        P( f'            if ( req_id_chosen == {i} ) req{i}_addr_i <= req_addr_i;' )
    P( f'        end else if ( xx2l0c_p_pvld && xx2l0c_p_prdy ) begin' )
    P( f'            xx2l0c_p_pvld <= 0;' )
    P( f'        end' ) 
    P( f'        req_got_status_mask <= (req_got_status_mask & ~req_issued_mask) | req_status_mask;' )
    P( f'        req_in_use_mask     <= (req_in_use_mask & ~(rdat_mask | req_status_must_retry_mask)) | req_issued_mask;' )
    P( f'        if ( l0c_idle && req_cnt === req_cnt_max && req_in_use_mask === 0 ) begin' )
    P( f'            $display( "PASS" );' )
    P( f'            $finish;' )
    P( f'        end' )
    P( f'    end' )
    P( f'end' )
    V.dassert( 'l0c_idle === 1 || (|req_in_use_mask) === 1', 'should be non-idle only if requests outstanding' )
    V.rega( 'xx2l0c_d_pvld', 1, 'xx2l0c_pvld' )
    V.dassert( 'l0c_idle === 0 || (xx2l0c_d_pvld == 0', 'should be non-idle when interfaces are busy' )
    V.dassert( '(req_status_mask & req_in_use_mask) === req_status_mask', 'status for req not outstanding' )
    V.dassert( '(req_status_mask & req_got_status_mask) === 0', 'status received twice' )
    V.dassert( '(req_status_is_hit_mask & rdat_mask) === req_status_is_hit_mask', 'is_hit with no data' )
    V.dassert( '(req_status_is_miss_mask & rdat_mask) === 0', 'is_miss with data at same time' )

    P()
    P(f'endmodule // tb_{module_name}' )
