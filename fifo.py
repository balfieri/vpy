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
# Check p and fill in defaults
#--------------------------------------------------------------------
def check( p ):
    if 'd' not in p: S.die( 'fifo.make: d not specified' )
    if p['d'] < 1: S.die( 'fifo.make: d must be >= 1' )
    if 'w' not in p: S.die( 'fifo.make: w not specified' )
    if p['w'] < 1: S.die( 'fifo.make: w must be >= 1' )

    if 'is_async' in p and p['is_async']: S.die( f'fifo.check: is_async=True is not currently allowed' )
    p['is_async'] = False
    if 'wr_clk' not in p: p['wr_clk'] = V.clk
    if 'rd_clk' not in p: p['rd_clk'] = V.clk
    if 'wr_reset_' not in p: p['wr_reset_'] = V.reset_
    if 'rd_reset_' not in p: p['rd_reset_'] = V.reset_

    if 'wr' not in p: p['wr'] = 'wr'
    if 'rd' not in p: p['rd'] = 'rd'

#--------------------------------------------------------------------
# Instantiates a fifo inline and arranges with V.py to have it generated during module_footer().
#--------------------------------------------------------------------
def stage( p, iname, oname, sigs, pvld='pvld', prdy='prdy', module_name='', inst_name='', with_wr_prdy=True, do_decl=True ):
    w = V.iface_width( sigs )
    if 'w' in p and p['w'] != w: S.die( f'fifo.stage: width w does not match expected sigs width of {w}' )
    p['w'] = w

    if 'module_name' == '': module_name = f'{V.module_name}_fifo_{d}x{w}'
    if 'wr' not in p and iname != '': p['wr'] = iname
    if 'rd' not in p and oname != '': p['rd'] = oname

    check( p )

    if inst_name == '': inst_name = 'u_' + module_name

    inst( p, inst_name, iname, oname, sigs, pvld, prdy, with_wr_prdy=with_wr_prdy, do_decl=do_decl )

    # add a callback to make() below to get the fifo generated during module_footer()
    V.post_modules[module_name] = { 'generator': make, 'p': p.copy() }

#--------------------------------------------------------------------
# Instantiates a fifo that is known to exist
#--------------------------------------------------------------------
def inst( p, module_name, inst_name, iname, oname, sigs, pvld='pvld', prdy='prdy', with_wr_prdy=True, do_decl=True, do_dprint=False ):
    P()
    names = ', '.join( sigs.keys() )
    d = p['d']
    w = p['w']
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
    
    wr_clk    = p['wr_clk']
    wr_reset_ = p['wr_reset_']
    P(f'{module_name} {inst_name}( .{wr_clk}({wr_clk}), .{wr_reset_}({wr_reset_}),' )
    if p['is_async']:
        rd_clk    = p['rd_clk']
        rd_reset_ = p['rd_reset_']
        P(f'                        .{rd_clk}({rd_clk}), .{rd_reset_}({rd_reset_},' )
    wr = p['wr']
    rd = p['rd']
    P(f'                        .{wr}_pvld({iname_pvld}), .{wr}_prdy({iname_prdy}), .{wr}_pd('+'{'+f'{ins}'+'}),' )
    P(f'                        .{rd}_pvld({oname_pvld}), .{rd}_prdy({oname_prdy}), .{rd}_pd('+'{'+f'{outs}'+'}) );' )
    if do_dprint:
        V.iface_dprint( iname, sigs, f'{wr_reset_} && {iname_pvld} && {iname_prdy}' )
        V.iface_dprint( oname, sigs, f'{wr_reset_} && {oname_pvld} && {iname_prdy}' )

#--------------------------------------------------------------------
# Generates a full fifo module.
#--------------------------------------------------------------------
def make( p, module_name, with_file_header=True ): 
    check( p )

    wr          = p['wr']
    rd          = p['rd']
    is_async    = p['is_async']
    wr_clk      = p['wr_clk']
    wr_reset_   = p['wr_reset_']
    rd_clk      = p['rd_clk']
    rd_reset_   = p['rd_reset_']

    V.module_header_begin( module_name, with_file_header=with_file_header )

    V.input(  wr_clk,         1 )
    V.input(  wr_reset_,      1 )
    if is_async:
        V.input( rd_clk,      1 )
        V.input( rd_reset_,   1 )
   
    V.input(  f'{wr}_pvld',   1 )
    V.output( f'{wr}_prdy',   1 )
    V.input(  f'{wr}_pd',     p['w'] )
    
    V.output( f'{rd}_pvld',   1 )
    V.input(  f'{rd}_prdy',   1 )
    V.output( f'{rd}_pd',     p['w'] )
    
    V.module_header_end( no_warn_filename=True )

    d = p['d']
    if d == 0:
        P(f'assign {{{wr}_prdy,{rd}_pvld,{rd}_pd}} = {{{rd}_prdy,{wr}_pvld,{wr}_pd}};' )
    elif d == 1:
        P()
        P(f'// simple flop' )
        P(f'//' )
        V.reg( f'{rd}_pvld', 1 )
        V.reg( f'{rd}_pd', p['w'] )
        V.always_at_posedge( _clk=wr_clk )
        P(f'    {rd}_pvld <= {wr}_pvld;' )
        P(f'    if ( {wr}_pvld ) {rd}_pd <= {wr}_pd;' )
        P(f'end' )
    else:
        w     = p['w']
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
    P(f'endmodule // {module_name}' )

#--------------------------------------------------------------------
# Generates a testbench module for a fifo module.
#--------------------------------------------------------------------
def make_tb( p, module_name, inst_name, sigs, do_dprint=True ):
    check( p )

    wr_reset_   = p['wr_reset_']
    wr          = p['wr']
    rd          = p['rd']

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
    inst( p, module_name, f'u_{inst_name}', wr, rd, sigs, do_dprint=do_dprint )

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
    V.reg( f'wr_dat', p['w'] )
    V.reg( f'rd_dat', p['w'] ) # expected
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

