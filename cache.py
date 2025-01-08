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
# cache.py - cache generator
#
import S
import V
import C # temporary

P = print

def check( params ):
    # TODO: do this and also propagate values and names down below
    pass

def inst( params, module_name, inst_name, do_decls ):
    check( params )
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

def make( params, module_name ):
    check( params )
    header( params, module_name )

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

    tags( f'tags', C.l0c_addr_w, C.l0c_slot_cnt, 1, C.l0c_ref_cnt_max )

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

#--------------------------------------------------------------------
# Generate cache module header
#--------------------------------------------------------------------
def header( params, module_name ):
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
  
#--------------------------------------------------------------------
# Generate cache tags handling.
#--------------------------------------------------------------------
def tags( name, addr_w, tag_cnt, req_cnt, ref_cnt_max, incr_ref_cnt_max=1, decr_req_cnt=0, can_always_alloc=False, custom_avails=False ):
    if incr_ref_cnt_max < 1: S.die( f'tags: incr_ref_cnt_max needs to be at least 1' )
    if decr_req_cnt == 0: decr_req_cnt = req_cnt

    P()
    P(f'// {name} cache tags: addr_w={addr_w} tag_cnt={tag_cnt} req_cnt={req_cnt} ref_cnt_max={ref_cnt_max}' )
    P(f'//' )
    tag_i_w = max( 1, V.log2( tag_cnt ) )
    req_i_w = max( 1, V.log2( req_cnt ) )
    name_uc = name.upper()
    V.enum( f'{name_uc}_', ['MISS_CANT_ALLOC', 'MISS', 'HIT', 'HIT_BEING_FILLED'] )
    ref_cnt_w = V.log2( ref_cnt_max+1 )
    for i in range(tag_cnt): V.reg( f'{name}__ref_cnt{i}', ref_cnt_w )
    V.reg( f'{name}__vlds', tag_cnt )
    for i in range(tag_cnt): V.reg( f'{name}__addr{i}', addr_w )
    V.reg( f'{name}__filleds', tag_cnt )

    P()
    P(f'// {name} hit checks' )
    P(f'//' )
    hits = ''
    needs_allocs = []
    for r in range(req_cnt):
        V.wirea( f'{name}_req{r}__hit_one_hot', tag_cnt, V.concata( [f'{name}_req{r}_pvld && {name}__vlds[{i}] && {name}_req{r}_addr == {name}__addr{i}' for i in range(tag_cnt)], 1 ) )
        V.one_hot_to_binary( f'{name}_req{r}__hit_one_hot', tag_cnt, f'{name}_req{r}__hit_i', f'{name}_req{r}__hit_vld' )
        V.wirea( f'{name}_req{r}_hit_and_filled', 1, f'{name}_req{r}__hit_vld && ({name}_req{r}__hit_one_hot & {name}__filleds) == {name}_req{r}__hit_one_hot' )
        V.wirea( f'{name}_req{r}__needs_alloc', 1, f'{name}_req{r}_pvld && !{name}_req{r}__hit_vld' )
        if r != 0: hits += ' | '
        hits += f'{name}_req{r}__hit_one_hot'
        needs_allocs.append( f'{name}_req{r}__needs_alloc' )
    V.wirea( f'{name}__hits', tag_cnt, hits )
    V.wirea( f'{name}__needs_allocs', req_cnt, V.concata( needs_allocs, 1 ) )

    P()
    P(f'// {name} alloc' )
    P(f'//' )
    V.wirea( f'{name}__need_alloc_pvld', 1, f'|{name}__needs_allocs' )
    if custom_avails:
        V.wire( f'{name}__avails', tag_cnt )
    else:
        avails = []
        for i in range(tag_cnt):
            avails.append( f'{name}__need_alloc_pvld && !{name}__hits[{i}] && {name}__ref_cnt{i} == 0' )
        V.wirea( f'{name}__avails', tag_cnt, V.concata( avails, 1 ) )
    V.choose_eligible( f'{name}__alloc_avail_chosen_i', f'{name}__avails', tag_cnt, f'{name}__avail_preferred_i', gen_preferred=True )
    V.wirea( f'{name}__alloc_pvld', 1, f'{name}__avails_any_vld' )
    V.choose_eligible( f'{name}__alloc_req_chosen_i',  f'{name}__needs_allocs', req_cnt, f'{name}__alloc_req_preferred_i', gen_preferred=True )
    addrs = [ f'{name}_req{i}_addr' for i in range(req_cnt) ]
    V.muxa( f'{name}__alloc_addr', addr_w, f'{name}__alloc_req_chosen_i', addrs )
    V.binary_to_one_hot( f'{name}__alloc_avail_chosen_i', tag_cnt, r=f'{name}__alloc_avail_chosen_one_hot', pvld=f'{name}__alloc_pvld' )
    V.always_at_posedge()
    P(f'    if ( !{V.reset_} ) begin' )
    P(f'        {name}__vlds <= 0;' )
    P(f'    end else begin' )
    for i in range(tag_cnt):
        P(f'        if ( {name}__alloc_pvld && {name}__alloc_avail_chosen_i == {i} ) begin' )
        P(f'            {name}__vlds[{i}] <= 1\'b1;' )
        P(f'            {name}__addr{i} <= {name}__alloc_addr;' )
        P(f'        end' )
    P(f'    end' )
    P(f'end' )

    P()
    P(f'// {name} statuses' )
    P(f'//' )
    for r in range(req_cnt):
        if can_always_alloc:
            V.wirea( f'{name}_req{r}_status', 2, f'{name}_req{r}_hit_and_filled ? {name_uc}_HIT : {name}_req{r}__hit_vld ? {name_uc}_HIT_BEING_FILLED : {name_uc}_MISS' )
            dassert( f'!{name}_req{r}__needs_alloc || ({name}__alloc_pvld && {name}__alloc_req_chosen_i == {i})', f'{name} has can_always_alloc=True but can\'t alloc for req{r}' )
        else:
            V.wirea( f'{name}_req{r}_status', 2, f'{name}_req{r}_hit_and_filled ? {name_uc}_HIT : {name}_req{r}__hit_vld ? {name_uc}_HIT_BEING_FILLED : ({name}__alloc_pvld && {name}__alloc_req_chosen_i == {r}) ? {name_uc}_MISS : {name_uc}_MISS_CANT_ALLOC' )
        V.wirea( f'{name}_req{r}_tag_i', tag_i_w, f'{name}_req{r}__hit_vld ? {name}_req{r}__hit_i : {name}__alloc_avail_chosen_i' )
        sigs = { 'addr': addr_w, 
                 'tag_i': tag_i_w,
                 'status': 2 }
        if incr_ref_cnt_max > 1: sigs['incr_cnt'] = V.log2(incr_ref_cnt_max+1)
        V.iface_dprint( f'{name}_req{r}', sigs, f'{name}_req{r}_pvld' )

    P()
    P(f'// {name} decrements' )
    P(f'//' )
    decrs = ''
    for r in range(decr_req_cnt):
        V.binary_to_one_hot( f'{name}_decr{r}_tag_i', tag_cnt, f'{name}_decr{r}__one_hot', f'{name}_decr{r}_pvld' )
        if r != 0: decrs += ' | '
        decrs += f'{name}_decr{r}__one_hot'
        V.iface_dprint( f'{name}_decr{r}', { 'tag_i': tag_i_w }, f'{name}_decr{r}_pvld' )
    V.wirea( f'{name}__decrs', tag_cnt, decrs )

    P()
    P(f'// {name} fill' )
    P(f'//' )
    V.binary_to_one_hot( f'{name}_fill_tag_i', tag_cnt, f'{name}__fills', f'{name}_fill_pvld' )
    V.iface_dprint( f'{name}_fill', { 'tag_i': tag_i_w }, f'{name}_fill_pvld' )

    P()
    P(f'// {name} ref_cnt updates' )
    P(f'//' )
    P(f'// {V.vlint_off_width}' )
    V.always_at_posedge()
    P(f'    if ( !{V.reset_} ) begin' )
    for i in range(tag_cnt): 
        P(f'        {name}__ref_cnt{i} <= 0;' )
    P(f'    end else begin' )
    for i in range(tag_cnt): 
        bool_expr = f'{name}__alloc_avail_chosen_one_hot[{i}]'
        sum_expr = f'{name}__ref_cnt{i}'
        sum_expr += f' + {name}__alloc_avail_chosen_one_hot[{i}]'
        for r in range(req_cnt):
            bool_expr += f' || {name}_req{r}__hit_one_hot[{i}]'
            sum_expr  += f' + {name}_req{r}__hit_one_hot[{i}]'
        for r in range(decr_req_cnt):
            bool_expr += f' || {name}_decr{r}__one_hot[{i}]'
            sum_expr  += f' - {name}_decr{r}__one_hot[{i}]'
        P(f'        if ( {bool_expr} ) begin' )
        P(f'            {name}__ref_cnt{i} <= {sum_expr};' )
        P(f'        end' )
    P(f'    end' )
    P(f'end' )
    P(f'// {V.vlint_on_width}' )

    P()
    P(f'// {name} filled updates' )
    P(f'//' )
    V.always_at_posedge()
    P(f'    if ( |{name}__alloc_avail_chosen_one_hot || {name}_fill_pvld ) begin' )
    P(f'        {name}__filleds <= (~{name}__alloc_avail_chosen_one_hot & {name}__filleds) | {name}__fills;' )
    P(f'    end' )
    P(f'end' )

    P()
    P(f'// {name} assertions' )
    P(f'//' )
    V.dassert_no_x( f'{name}__vlds' )
    V.dassert_no_x( f'{name}__filleds & {name}__vlds' )
    V.dassert_no_x( f'{name}__hits' )
    V.dassert_no_x( f'{name}__alloc_avail_chosen_one_hot' )
    V.dassert_no_x( f'{name}__fills' )
    V.dassert_no_x( f'{name}__decrs' )
    V.dassert( f'({name}__hits & {name}__alloc_avail_chosen_one_hot) === {tag_cnt}\'d0', f'{name} has hit and alloc to the same slot' )
    V.dassert( f'({name}__fills & {name}__filleds) === {tag_cnt}\'d0', f'{name} has fill of already filled slot' )
    V.dassert( f'({name}__decrs & {name}__vlds) === {name}__decrs', f'{name} has decr-ref-cnt of slot with ref_cnt==0' )
    for i in range(tag_cnt):
        V.dassert( f'{name}__ref_cnt{i} !== 0 || {name}_decr{r}__one_hot[{i}] === 0 || {name}_req{r}__hit_one_hot[{i}] == 1', f'{name}__ref_cnt{i} underflow' )
        V.dassert( f'{name}__alloc_avail_chosen_one_hot[{i}] === 0 || {name}_req{r}__hit_one_hot[{i}] === 0', f'{name}__ref_cnt{i} alloc and hit at same time' )
        V.dassert( f'{name}__ref_cnt{i} !== {ref_cnt_max} || ({name}__alloc_avail_chosen_one_hot[{i}] === 0 && {name}_req{r}__hit_one_hot[{i}] === 0)', f'{name}__ref_cnt{i} overflow' )
    expr = ''
    for i in range(tag_cnt-1):
        for j in range(i+1, tag_cnt):
            if expr != '': expr += ' && '
            expr += f'(!{name}__vlds[{i}] || !{name}__vlds[{j}] || {name}__addr{i} !== {name}__addr{j})'
    V.dassert( f'{expr}', f'{name} has duplicate tags' )

    P()
    P(f'// {name} idle' )
    P(f'//' )
    idle = f'!{name}_fill_pvld'
    for i in range(tag_cnt): idle += f' && {name}__ref_cnt{i} == 0'
    for r in range(req_cnt): idle += f' && !{name}_req{r}_pvld' 
    V.wirea( f'{name}_idle', 1, idle )

#--------------------------------------------------------------------
# Generate cache testbench
#--------------------------------------------------------------------
def make_tb( params, module_name, inst_name ):
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

    inst( params, module_name, f'u_{inst_name}', True )

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
