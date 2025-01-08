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
import C
import cache

P = print

def reinit():
    # I am confused about subword cnt from C.py
    params = { # required:
               'is_read_only':  1,              # read-only cache
               'line_cnt':      2,              # number of lines
               'assoc':         2,              # fully associative (one set)
               'line_w':        32,             # width of line (dat)
               'addr_w':        32,             # width of virtual byte address
               'req_id_w':      3,              # width of req_id in request

               # optional:
               'cache_name':    'l0c',          # short name used in interfaces
               'req_name':      'xx',           # short name used in interfaces
               'mem_name':      'mem',          # short name used in interfaces
               'tag_ram_kind':  'ff',           # tag ram in flops
               'data_ram_kind': 'ff',           # data ram in flops
               'req_cnt':       1,              # number of request interfaces
               'subword_cnt':   1,              # number of subwords in dat
               'mem_dat_w':     64,             # width of memory dat (default is line_w)
             }

def header( module_name ):
    P(f'// L0 read-only cache with the following properties:' )
    P(f'// - tags and data kept in flops' )
    P(f'// - fully-associative' )
    P(f'// - {C.l0c_slot_cnt} lines, {C.l0c_line_w}-bit line width, which is the same as the per-request data word width' )
    P(f'// - {C.addr_w}-bit request byte address, but this is shorted according to the request word width ' )
    P(f'// - each request has an associated {C.l0c_req_id_w}-bit req_id to help the requestor identify the return information' )
    P(f'// - requests are non-blocking, and a req status return interface indicates is_hit, is_miss, and must_retry' )
    P(f'// - must_retry=1 means the cache cannot currently allocate a line OR a hit-under-miss situation' )
    P(f'// - any must_retry request must be retried by the requestor, obviously' )
    P(f'// - data is returned out-of-order, consistent with non-blocking requests' )
    P(f'// - {C.mem_dat_w}-bit memory read return data width' )
    P(f'// - maximum per-line reference count of {C.l0c_ref_cnt_max}' )
    P(f'//' )
    V.module_header_begin( module_name )
    V.input( f'{V.clk}', 1 )
    V.input( f'{V.reset_}', 1 )
    V.output( f'l0c_idle', 1 )
    V.iface_input( f'xx2l0c', C.xx2l0c, True )
    V.iface_output( f'l0c2xx_status', C.l0c2xx_status, False )
    V.iface_output( f'l0c2xx_dat', C.l0c2xx_dat, False )
    V.iface_output( f'l0c2mem', C.l0c2mem, True )
    V.iface_input( f'mem2l0c', C.mem2l0c, False )
    V.module_header_end()
    V.wire( f'xx2l0c_d_prdy', 1 )
    V.iface_stage( f'xx2l0c', f'xx2l0c_d', C.xx2l0c, 'pvld', 'prdy', full_handshake=True, do_dprint=False )
    P()
    V.iface_wire( f'l0c2mem_p', C.l0c2mem, True )
    V.iface_stage( f'l0c2mem_p', f'l0c2mem', C.l0c2mem, 'pvld', 'prdy', full_handshake=True, do_dprint=False )
    V.iface_stage( f'mem2l0c', f'mem2l0c_d', C.mem2l0c, 'pvld', do_dprint=False )
    V.iface_dprint( f'xx2l0c', C.xx2l0c, f'xx2l0c_pvld', f'xx2l0c_prdy' )
    V.iface_dprint( f'l0c2xx_status', C.l0c2xx_status, f'l0c2xx_status_pvld' )
    V.iface_dprint( f'l0c2xx_dat', C.l0c2xx_dat, f'l0c2xx_dat_pvld' )
    V.iface_dprint( f'l0c2mem', C.l0c2mem, f'l0c2mem_pvld', f'l0c2mem_prdy' )
    V.iface_dprint( f'mem2l0c', C.mem2l0c, f'mem2l0c_pvld' )
  
def inst_cache1( module_name, inst_name, do_decls ):
    if do_decls: 
        V.wire( f'l0c_idle', 1 )
        V.iface_wire( f'xx2l0c', C.xx2l0c, True, True )
        V.iface_wire( f'l0c2xx_status', C.l0c2xx_status, True, False )
        V.iface_wire( f'l0c2xx_dat', C.l0c2xx_dat, True, False )
        V.iface_wire( f'l0c2mem', C.l0c2mem, True, True )
        V.iface_wire( f'mem2l0c', C.mem2l0c, True, False )
    P()
    P(f'{module_name} {inst_name}(' ) 
    P(f'      .{V.clk}({V.clk}), .{V.reset_}({V.reset_}), .l0c_idle(l0c_idle)' )
    V.iface_inst( f'xx2l0c', f'xx2l0c', C.xx2l0c, True, True )
    V.iface_inst( f'l0c2xx_status', f'l0c2xx_status', C.l0c2xx_status, True, False )
    V.iface_inst( f'l0c2xx_dat', f'l0c2xx_dat', C.l0c2xx_dat, True, False )
    V.iface_inst( f'l0c2mem', f'l0c2mem', C.l0c2mem, True, True )
    V.iface_inst( f'mem2l0c', f'mem2l0c', C.mem2l0c, True, False )
    P(f'    );' )

def make_cache1( module_name ):
    header( module_name )

    P()
    P( f'// TAGS INPUTS' )
    P( f'//' )
    P( f'assign xx2l0c_d_prdy = l0c2mem_p_prdy && !mem2l0c_d_pvld;' )
    V.wirea( f'tags_req0_pvld', 1, f'xx2l0c_d_pvld && xx2l0c_d_prdy' )
    V.wirea( f'tags_req0_addr', C.l0c_addr_w, f'xx2l0c_d_addr' )
    V.wire( f'tags_decr0_pvld', 1 )
    V.wire( f'tags_decr0_tag_i', C.l0c_slot_id_w )
    V.wirea( f'tags_fill_pvld', 1, f'mem2l0c_d_pvld' )
    V.wirea( f'tags_fill_tag_i', C.l0c_slot_id_w, f'mem2l0c_d_tag_id[{C.l0c_slot_id_w-1}:0]' )
    V.wirea( f'tags_fill_subword_i', C.l0c_subword_w, f'mem2l0c_d_tag_id[{C.l0c_subword_w+C.l0c_slot_id_w-1}:{C.l0c_slot_id_w}]' )
    V.wirea( f'tags_fill_req_id', C.l0c_req_id_w, f'mem2l0c_d_tag_id[{C.l0c_mem_tag_id_w-1}:{C.l0c_subword_w+C.l0c_slot_id_w}]' )
    V.mux_subword( f'tags_fill_dat', C.l0c_dat_w, f'tags_fill_subword_i', f'mem2l0c_d_dat', C.mem_dat_w )

    cache.tags( f'tags', C.l0c_addr_w, C.l0c_slot_cnt, 1, C.l0c_ref_cnt_max )

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
    P( f'// CACHED DATA' )
    P( f'//' )
    for i in range(C.l0c_slot_cnt): V.reg( f'l0c_bits{i}', C.l0c_dat_w )
    V.always_at_posedge()
    for i in range(C.l0c_slot_cnt): P( f'    if ( tags_fill_pvld && tags_fill_tag_i == {i} ) l0c_bits{i} <= tags_fill_dat;' )
    P( f'end' )

    P()
    P( f'// MEM REQ' )
    P( f'//' )
    P( f'assign l0c2mem_p_pvld = tags_req0_pvld && tags_req0_status == TAGS_MISS;' )
    P( f'assign l0c2mem_p_addr = tags_req0_addr[{C.l0c_addr_w-1}:{C.l0c_subword_w}];' )
    V.wirea( f'l0c2mem_p_subword_i', C.l0c_subword_w, f'tags_req0_addr[{C.l0c_subword_w-1}:0]' )
    P( f'assign l0c2mem_p_tag_id = {{xx2l0c_d_req_id, l0c2mem_p_subword_i, tags__alloc_avail_chosen_i}};' )

    P()
    P( f'// RETURNED DATA' )
    P( f'//' )
    V.iface_reg( f'l0c2xx_dat', C.l0c2xx_dat, True, False )
    V.wirea( f'l0c2xx_dat_pvld_p', 1, f'tags_fill_pvld || (tags_req0_pvld && tags_req0_status == TAGS_HIT)' )
    P( f'assign tags_decr0_pvld = l0c2xx_dat_pvld_p || (tags_req0_pvld && tags_req0_status == TAGS_HIT_BEING_FILLED);' )
    P( f'assign tags_decr0_tag_i = tags_fill_pvld ? tags_fill_tag_i : tags_req0__hit_i;' )
    dats = [f'l0c_bits{i}' for i in range(C.l0c_slot_cnt)]
    V.muxa( f'l0c_hit_dat', C.l0c_dat_w, f'tags_req0__hit_i', dats )
    V.always_at_posedge()
    P( f'    l0c2xx_dat_pvld <= l0c2xx_dat_pvld_p;' )
    P( f'    if ( l0c2xx_dat_pvld_p ) begin' )
    P( f'        l0c2xx_dat_req_id <= tags_fill_pvld ? tags_fill_req_id : xx2l0c_d_req_id;' )
    P( f'        l0c2xx_dat_dat <= tags_fill_pvld ? tags_fill_dat : l0c_hit_dat;' )
    P( f'    end' )
    P( f'end' )

    P()
    P( f'// IDLE' )
    P( f'//' )
    idle = '!xx2l0c_d_pvld && !l0c2mem_p_pvld && !mem2l0c_d_pvld && tags_idle'
    P( f'assign l0c_idle = {idle};' )

    V.module_footer( module_name )

def make_tb_cache1( name, module_name ):
    P(f'// Testbench for {module_name}.v with the following properties beyond those of the cache:' )
    P(f'// - issues a plusarg-selectable number of requests (default: 100)' )
    P(f'// - randomly selects an address from {C.l0c_tb_addr_cnt} possible random addresses (to induce hits)' )
    P(f'// - supplies a memory model that returns data that includes the memory address and line subword index for each line data' )
    P(f'// - checks that returned data from cache matches the expected data for the line' )
    P(f'// - randomly adds bubbles in the request stream' )
    P(f'// - randomly stalls the memory requests out of the cache' )
    P(f'//' )
    V.module_header_begin( f'tb_{module_name}' )
    V.module_header_end()
    P()
    V.tb_clk()
    V.tb_reset_()
    V.tb_dump( f'tb_{module_name}', include_saif=False )
    P()
    V.tb_rand_init()

    inst_cache1( module_name, f'u_{name}', True )

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
    V.binary_to_one_hot( 'l0c2xx_dat_req_id',    C.l0c_req_id_cnt, 'rdat_mask',                  f'l0c2xx_dat_pvld' )
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
    V.rega( 'mem2l0c_d_pvld', 1, 'mem2l0c_pvld' )
    V.dassert( 'l0c_idle === 0 || (xx2l0c_d_pvld == 0 && l0c2mem_pvld === 0 && mem2l0c_d_pvld === 0)', 'should be non-idle when interfaces are busy' )
    V.dassert( '(req_status_mask & req_in_use_mask) === req_status_mask', 'status for req not outstanding' )
    V.dassert( '(req_status_mask & req_got_status_mask) === 0', 'status received twice' )
    V.dassert( '(req_status_is_hit_mask & rdat_mask) === req_status_is_hit_mask', 'is_hit with no data' )
    V.dassert( '(req_status_is_miss_mask & rdat_mask) === 0', 'is_miss with data at same time' )
    V.dassert( '(rdat_mask & req_in_use_mask) === rdat_mask', 'dat returned for req not outstanding' )
    V.muxa( 'rdat_req_addr_i', C.l0c_tb_addr_id_w, 'l0c2xx_dat_req_id', req_addr_is )
    V.muxa( 'rdat_dat_expected', C.l0c_dat_w, 'rdat_req_addr_i', dats_expected )
    V.dassert( '!l0c2xx_dat_pvld || (l0c2xx_dat_dat === rdat_dat_expected)', 'unexpected dat returned' )

    P()
    P( f'// MEM RETURNS - just use addr to construct unique data for now' )
    P( f'//' )
    V.tb_randbits( 'l0c2mem_prdy_p', 1 )
    P( f'assign l0c2mem_prdy = !{V.reset_} || l0c2mem_prdy_p;' )
    P( f'assign mem2l0c_pvld = l0c2mem_pvld && l0c2mem_prdy;' )
    P( f'assign mem2l0c_tag_id = l0c2mem_tag_id;' )
    dat_s = ''
    extra_w = C.l0c_dat_w - C.mem_addr_w - C.l0c_subword_w
    for i in range(C.l0c_subword_cnt):
        comma = ',' if dat_s != '' else ''
        extra = f'{extra_w}\'d0,' if extra_w > 0 else ''
        dat_s = f'{extra}l0c2mem_addr,{C.l0c_subword_w}\'d{i}{comma}{dat_s}'
    P( f'assign mem2l0c_dat = {{{dat_s}}};' )

    P()
    P(f'endmodule // tb_{module_name}' )
