# Copyright (c) 2017-2024 Robert A. Alfieri
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

P = print

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
# Check that filling a cache tag that expects it.
#--------------------------------------------------------------------
def cache_filled_check( name, tag_i, r, tag_cnt, add_reg=True ):
    V.mux_subword( r, 1, tag_i, f'{name}__filleds', tag_cnt, add_reg=add_reg )
    

