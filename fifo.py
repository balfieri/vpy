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
# fifo.py - fifo generator
#
import S
import V

P = print

#--------------------------------------------------------------------
# Check params and fill in defaults
#--------------------------------------------------------------------
def check( params ):
    if 'd' not in params: S.die( 'fifo.make: d not specified' )
    if params['d'] < 1: S.die( 'fifo.make: d must be >= 1' )
    if 'w' not in params: S.die( 'fifo.make: w not specified' )
    if params['w'] < 1: S.die( 'fifo.make: w must be >= 1' )

    if 'm_name' not in params: s.die( f'fifo.check: m_name is not specified' )

    if 'is_async' in params and params['is_async']: S.die( f'fifo.check: is_async=True is not currently allowed' )
    params['is_async'] = False
    if 'wr_clk' not in params: params['wr_clk'] = V.clk
    if 'rd_clk' not in params: params['rd_clk'] = V.clk
    if 'wr_reset_' not in params: params['wr_reset_'] = V.reset_
    if 'rd_reset_' not in params: params['rd_reset_'] = V.reset_

    if 'wr' not in params: params['wr'] = 'wr'
    if 'rd' not in params: params['rd'] = 'rd'

#--------------------------------------------------------------------
# Instantiates a fifo inline and arranges with V.py to have it generated during module_footer().
#--------------------------------------------------------------------
def stage( params, iname, oname, sigs, pvld='pvld', prdy='prdy', inst_name='', with_wr_prdy=True, do_decl=True ):
    w = V.iface_width( sigs )
    if 'w' in params and params['w'] != w: S.die( f'fifo.stage: width w does not match expected sigs width of {w}' )
    params['w'] = w

    if 'm_name' not in params: params['m_name'] = f'{V.module_name}_fifo_{d}x{w}'
    if 'wr' not in params and iname != '': params['wr'] = iname
    if 'rd' not in params and oname != '': params['rd'] = oname

    check( params )

    if inst_name == '': inst_name = 'u_' + params['m_name']

    inst_fifo( fifos[m_name], inst_name, iname, oname, sigs, pvld, prdy, with_wr_prdy=with_wr_prdy, do_decl=do_decl )

    # add a callback to make() below to get the fifo generated during module_footer()
    V.post_modules[m_name] = { 'generator': make, 'params': params.copy() }

#--------------------------------------------------------------------
# Instantiates a fifo that is known to exist
#--------------------------------------------------------------------
def inst( params, inst_name, iname, oname, sigs, pvld='pvld', prdy='prdy', with_wr_prdy=True, do_decl=True, do_dprint=False ):
    P()
    names = ', '.join( sigs.keys() )
    d = params['d']
    w = params['w']
    P(f'// {d}x{w} fifo for: {names}' )
    P(f'//' )

    ins = ''
    outs = ''
    iname_pvld = f'{iname}_{pvld}'
    iname_prdy = f'{iname}_{prdy}'
    oname_pvld = f'{oname}_{pvld}'
    oname_prdy = f'{oname}_{prdy}'
    if with_wr_prdy: 
        if do_decl: V.wire( iname_prdy, 1 )
    else:
        iname_prdy = ''
    if do_decl: V.wire( oname_pvld, 1 )
    if do_decl: V.wire( oname_prdy, 1 )
    for sig in sigs:
        if do_decl: V.wire( f'{oname}_{sig}', sigs[sig] )
        if ins  != '': ins  += ', '
        if outs != '': outs += ', '
        ins  += f'{iname}_{sig}'
        outs += f'{oname}_{sig}'
    
    m_name    = params['m_name']
    wr_clk    = params['wr_clk']
    wr_reset_ = params['wr_reset_']
    P(f'{m_name} {inst_name}( .{wr_clk}({wr_clk}), .{wr_reset_}({wr_reset_}),' )
    if params['is_async']:
        rd_clk    = params['rd_clk']
        rd_reset_ = params['rd_reset_']
        P(f'                        .{rd_clk}({rd_clk}), .{rd_reset_}({rd_reset_},' )
    wr = params['wr']
    rd = params['rd']
    P(f'                        .{wr}_pvld({iname_pvld}), .{wr}_prdy({iname_prdy}), .{wr}_pd('+'{'+f'{ins}'+'}),' )
    P(f'                        .{rd}_pvld({oname_pvld}), .{rd}_prdy({oname_prdy}), .{rd}_pd('+'{'+f'{outs}'+'}) );' )
    if do_dprint:
        V.iface_dprint( iname, sigs, f'{wr_reset_} && {iname_pvld} && {iname_prdy}' )
        V.iface_dprint( oname, sigs, f'{wr_reset_} && {oname_pvld} && {iname_prdy}' )

#--------------------------------------------------------------------
# Generates a full fifo module.
#--------------------------------------------------------------------
def make( params, with_file_header=True ): 
    check( params )

    m_name      = params['m_name']
    wr          = params['wr']
    rd          = params['rd']
    is_async    = params['is_async']
    wr_clk      = params['wr_clk']
    wr_reset_   = params['wr_reset_']
    rd_clk      = params['rd_clk']
    rd_reset_   = params['rd_reset_']

    V.module_header_begin( m_name, with_file_header=with_file_header )

    V.input(  wr_clk,         1 )
    V.input(  wr_reset_,      1 )
    if is_async:
        V.input( rd_clk,      1 )
        V.input( rd_reset_,   1 )
   
    V.input(  f'{wr}_pvld',   1 )
    V.output( f'{wr}_prdy',   1 )
    V.input(  f'{wr}_pd',     params['w'] )
    
    V.output( f'{rd}_pvld',   1 )
    V.input(  f'{rd}_prdy',   1 )
    V.output( f'{rd}_pd',     params['w'] )
    
    V.module_header_end( no_warn_filename=True )

    d = params['d']
    if d == 0:
        P(f'assign {{{wr}_prdy,{rd}_pvld,{rd}_pd}} = {{{rd}_prdy,{wr}_pvld,{wr}_pd}};' )
    elif d == 1:
        P()
        P(f'// simple flop' )
        P(f'//' )
        V.reg( f'{rd}_pvld', 1 )
        V.reg( f'{rd}_pd', params['w'] )
        V.always_at_posedge( _clk=wr_clk )
        P(f'    {rd}_pvld <= {wr}_pvld;' )
        P(f'    if ( {wr}_pvld ) {rd}_pd <= {wr}_pd;' )
        P(f'end' )
    else:
        w     = params['w']
        a_w   = V.log2( d )
        cnt_w = a_w
        cnt_w = (a_w+1) if (1 << a_w) >= d else a_w
        P(f'// flop ram' )
        P(f'//' )
        for i in range( d ): V.reg( f'ram_ff{i}', w )
        P()
        P(f'// PUSH/POP' )
        P(f'//' ) 
        V.reg( f'cnt', cnt_w )
        P(f'wire {wr}_pushing = {wr}_pvld && {wr}_prdy;' )
        P(f'wire {rd}_popping = {rd}_pvld && {rd}_prdy;' )
        V.always_at_posedge( _clk=wr_clk )
        P(f'    if ( !{wr_reset_} ) begin' )
        P(f'        cnt <= 0;' )
        P(f'    end else if ( {wr}_pushing != {rd}_popping ) begin' )
        P(f'        // {V.vlint_off_width}' )
        P(f'        cnt <= cnt + {wr}_pushing - {rd}_popping;' )
        P(f'        // {V.vlint_on_width}' )
        P(f'    end' )
        P(f'end' )
        P()
        P(f'// WRITE SIDE' )
        P(f'//' ) 
        V.reg( f'{wr}_adr', a_w )
        P(f'assign {wr}_prdy = cnt != {d} || {rd}_popping;' )
        V.always_at_posedge( _clk=wr_clk )
        P(f'    if ( !{wr_reset_} ) begin' )
        P(f'        {wr}_adr <= 0;' )
        P(f'    end else if ( {wr}_pushing ) begin' )
        P(f'        // {V.vlint_off_caseincomplete}' )
        P(f'        case( {wr}_adr )' )
        for i in range( d ): P(f'            {a_w}\'d{i}: ram_ff{i} <= {wr}_pd;' )
        P(f'        endcase' )
        P(f'        // {V.vlint_on_caseincomplete}' )
        P()
        P(f'        {wr}_adr <= ({wr}_adr == {d-1}) ? 0 : ({wr}_adr+1);' )
        P(f'    end' )
        P(f'end' )
        P()
        P(f'// READ SIDE' )
        P(f'//' )
        V.reg( f'{rd}_adr', a_w )
        V.always_at_posedge( _clk=rd_clk )
        P(f'    if ( !{rd_reset_} ) begin' )
        P(f'        {rd}_adr <= 0;' )
        P(f'    end else if ( {rd}_popping ) begin' )
        P(f'        {rd}_adr <= ({rd}_adr == {d-1}) ? 0 : ({rd}_adr+1);' )
        P(f'    end' )
        P(f'end' )
        P()
        P(f'assign {rd}_pvld = cnt != 0;' )
        P(f'reg [{w-1}:0] {rd}_pd_p;' )
        P(f'assign {rd}_pd = {rd}_pd_p;' )
        P(f'always @( * ) begin' )
        P(f'    // {V.vlint_off_caseincomplete}' )
        P(f'    case( {rd}_adr )' )
        for i in range( d ): P(f'        {a_w}\'d{i}: {rd}_pd_p = ram_ff{i};' )
        P(f'        // VCS coverage off' )
        P(f'        default: begin' )
        P(f'            {rd}_pd_p = {w}\'d0;' )
        P(f'            // synopsys translate_off' )
        P(f'            {rd}_pd_p = {{{w}{{1\'bx}}}};' )
        P(f'            // synopsys translate_on' )
        P(f'            end' )
        P(f'        // VCS coverage on' )
        P(f'    endcase' )
        P(f'    // {V.vlint_on_caseincomplete}' )
        P(f'end' )
    P()
    P(f'endmodule // {m_name}' )

#--------------------------------------------------------------------
# Generates a testbench module for a fifo module.
#--------------------------------------------------------------------
def make_tb( name, params, sigs, do_dprint=True ):
    check( params )

    module_name = params['m_name']
    wr_reset_   = params['wr_reset_']
    wr          = params['wr']
    rd          = params['rd']

    P(f'// Testbench for {module_name}.v with the following properties beyond those of the fifo:' )
    P(f'// - incrementing input data' )
    P(f'// - randomly adds bubbles to write-side input' )
    P(f'// - randomly stalls the read-side output' )
    P(f'// - makes some assumptions that will need to be generalized later' )
    P(f'//' )
    V.module_header_begin( f'tb_{module_name}' )
    V.module_header_end()
    P()
    V.tb_clk()
    V.tb_reset_()
    V.tb_dump( f'tb_{module_name}', include_saif=False )
    P()
    V.tb_rand_init()

    V.iface_wire( wr, sigs, True, False )
    inst( params, f'u_{name}', wr, rd, sigs, do_dprint=do_dprint )

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
    V.reg( f'wr_dat', params['w'] )
    V.reg( f'rd_dat', params['w'] ) # expected
    P( f'assign {wr}_pvld = can_wr && wr_cnt < wr_cnt_max;' )
    P( f'assign {wr}_dat  = wr_dat;' )
    P( f'assign {rd}_prdy = can_rd;' )
    P( f'wire fifo_idle = !{wr}_pvld && !{rd}_pvld;' )
    V.always_at_posedge()
    P( f'    if ( !{wr_reset_} ) begin' )
    P( f'        wr_cnt <= 0;' )
    P( f'        rd_cnt <= 0;' )
    P( f'        wr_dat <= 0;' )
    P( f'        rd_dat <= 0;' )
    P( f'    end else begin' )
    P( f'        if ( {wr}_pvld && {wr}_prdy ) begin' )
    P( f'            wr_dat <= wr_dat + 1;' )
    P( f'            wr_cnt <= wr_cnt + 1;' )
    P( f'        end' )
    P( f'        if ( {rd}_pvld && {rd}_prdy ) begin' )
    P( f'            rd_dat <= rd_dat + 1;' )
    P( f'            rd_cnt <= rd_cnt + 1;' )
    P( f'        end' )
    P( f'        if ( fifo_idle && rd_cnt === wr_cnt_max ) begin' )
    P( f'            $display( "PASS" );' )
    P( f'            $finish;' )
    P( f'        end' )
    P( f'    end' )
    P( f'end' )
    V.dassert( f'{rd}_pvld === 0 || {rd}_dat === rd_dat', f'unexpected read data' )

    P()
    P(f'endmodule // tb_{module_name}' )

