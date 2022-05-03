# Copyright (c) 2017-2021 Robert A. Alfieri
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
# V.py - utility functions for generating Verilog
#
import S

P = print

def reinit( _clk='clk', _reset_='reset_', _vdebug=True, _vassert=True, _ramgen_cmd='' ):
    global clk, reset_, vdebug, vassert, ramgen_cmd
    global module_name, rams, fifos
    global seed_z_init, seed_w_init, seed_i
    global custom_cla
    global io
    global in_module_header
    global vlint_off_width, vlint_on_width
    global vlint_off_unused, vlint_on_unused
    clk = _clk
    reset_ = _reset_
    vdebug = _vdebug
    vassert = _vassert
    ramgen_cmd = _ramgen_cmd
    module_name = ''
    io = []
    in_module_header = False
    rams = {}
    fifos = {}
    seed_z_init = 0x12345678
    seed_w_init = 0xbabecaf3
    seed_i = 0
    custom_cla = False
    vlint_off_width  = 'verilator lint_off WIDTH' 
    vlint_on_width   = 'verilator lint_on WIDTH' 
    vlint_off_unused = 'verilator lint_off UNUSED' 
    vlint_on_unused  = 'verilator lint_on UNUSED' 

#-------------------------------------------
# Returns number of bits to hold 0 .. n-1
#-------------------------------------------
def log2( n ):
    n = 2*n - 1
    r = 0
    while n > 1:
        r += 1
        n >>= 1
    return r

def is_pow2( n ):
    return (1 << log2(n)) == n

#-------------------------------------------
# Returns number of bits to hold n, which is max(1, log2( n + 1 ))
#-------------------------------------------
def value_bitwidth( n ):
    return max( 1, log2( n + 1 ) )

def module_header_begin( mn ):
    global module_name
    module_name = mn
    global rams, fifos
    global io
    global in_module_header
    if in_module_header: S.die( 'module_header_begin() called while already in a module header' )
    rams = {}
    fifos = {}
    P(f'// AUTOMATICALLY GENERATED - DO NOT EDIT OR CHECK IN' )
    P()
    P(f'`timescale 1ns/1ps' )
    P()
    io = []
    in_module_header = True

def decl( kind, name, w, is_io=False ):     
    if w <= 0: S.die( f'{kind} {name} has width {w}' )
    global io
    if is_io:
        io.append( { 'name': name, 'kind': kind, 'width': w } )
    else:
        P( kind + ' ' + (('[' + str(w-1) + ':' + '0] ') if w != 1 else '') + name + ';' )

def decla( kind, name, w, v ):
    if w <= 0: S.die( f'{kind} {name} has width {w}' )
    P( kind + ' ' + (('[' + str(w-1) + ':' + '0] ') if w != 1 else '') + name + ' = ' + f'{v}' + ';' )

def input( name, w ):      
    decl( 'input ', name, w, True )

def sinput( name, w ):     
    decl( 'input signed ', name, w, True )

def output( name, w ):     
    decl( 'output', name, w, True )

def soutput( name, w ):    
    decl( 'output signed', name, w, True )

def wire( name, w ):       decl( 'wire', name, w )
def wirea( name, w, v ):   decla( 'wire', name, w, v )
def swire( name, w ):      decl( 'wire signed', name, w )
def swirea( name, w, v ):  decla( 'wire signed', name, w, v )
def reg( name, w ):        decl( 'reg', name, w )
def rega( name, w, v ):    
    reg( name, w )    
    always_at_posedge( f'{name} <= {v};' )
def sreg( name, w ):       decl( 'reg signed', name, w )
def srega( name, w, v ):    
    sreg( name, w )    
    always_at_posedge( f'{name} <= {v};' )

def module_header_end():
    global in_module_header
    global io
    if not in_module_header: S.die( 'module_header_end() called while not already in a module header' )
    ports_s = ''
    io_s = ''
    for i in range( len(io) ):
        if io[i]['name'] != '':
            if i != 0: ports_s += ', '
            ports_s += io[i]['name']

    if ports_s != '': ports_s = f'( {ports_s} )'

    P()
    if ports_s == '': 
        P(f'`ifndef VERILATOR' )
    P(f'module {module_name}{ports_s};' )
    if ports_s == '': 
        P(f'`else' )
        P(f'module {module_name}( {clk} );' )
        P(f'input {clk};' )
        P(f'`endif' )
    P()
    for i in range( len(io) ):
        if io[i]['name'] != '':
            w = io[i]['width']
            P( io[i]['kind'] + ' ' + (('[' + str(w-1) + ':' + '0] ') if w != 1 else '') + io[i]['name'] + ';' )
        else:
            P()
    in_module_header = False
    io = []

def enum( prefix, names ):
    cnt = len(names)
    if cnt == 0: S.die( f'no enums' )
    w = log2(cnt) if cnt > 1 else 1
    for i in range(cnt):
        wirea( f'{prefix}{names[i]}', w, i )
    return w

def enums_parse( file_name, prefix ):
    enums = {}
    if not S.file_exists( file_name ): S.die( f':enums_parse: {file_name} does not exist' )
    with open( file_name ) as my_file:
        for line in my_file:
            m = S.match( line, f'^wire .* ({prefix}\w+) = (\d+);' )
            if m:
                name = m.group( 1 )
                val  = int( m.group( 2 ) )
                enums[name] = val
    if len( enums ) == 0: die( f'enums_parse: {file_name} contains no enums with the prefix "{prefix}"' )
    return enums

def display( msg, sigs, use_hex_w=16, prefix='        ', show_module=False ):
    fmt = ''
    vals = ''
    for sig in sigs:
        w = sigs[sig][0] if isinstance( sigs[sig], list ) else sigs[sig] 
        if w == 0:
            fmt += sig # just text
        else:
            if w > 0: 
                fmt += f' {sig}='
            else:
               w = -w
            if w >= use_hex_w:
                wh = int( (w + 3) / 4 )
                fmt  += f'0x%0{wh}h'
            else:
                fmt  += f'%-d'
            vals += f', {sig}'
    while len( msg ) < 30: msg += ' '
    fmt = f'%0d: {msg}: {fmt}'
    if show_module: fmt += '   in %m'
    P( f'{prefix}$display( "{fmt}", $stime{vals} );' )

def dprint( msg, sigs, pvld, use_hex_w=16, with_clk=True, indent='' ):
    if not vdebug: return
    P(f'// synopsys translate_off' )
    prefix = indent
    if with_clk: prefix += f'always @( posedge {clk} ) '
    if pvld != '': prefix += f'if ( {pvld} ) '
    display( msg, sigs, use_hex_w, prefix )
    P(f'// synopsys translate_on' )

def dassert( expr, msg, pvld='', with_clk=True, indent='    ', if_fatal='' ):
    if not vassert: return
    P(f'// synopsys translate_off' )
    if with_clk: always_at_posedge()
    reset_test = f'{reset_} === 1\'b1 && ' if with_clk else ''
    pvld_test  = f'({pvld}) && '             if pvld != '' else ''
    P(f'{indent}if ( {reset_test}{pvld_test}(({expr}) !== 1\'b1) ) begin' )
    P(f'{indent}    $display( "%0d: ERROR: {msg}", $stime );' )
    P(f'{indent}    {if_fatal}$fatal;' )
    P(f'{indent}end' )
    if with_clk: P(f'end' )
    P(f'// synopsys translate_on' )
   
def dassert_no_x( expr, pvld='', with_clk=True, indent='    ', if_fatal='' ):
    dassert( f'^({expr}) !== 1\'bx', f'found an X in: {expr}', pvld, with_clk, indent, if_fatal )

#-------------------------------------------
# Common Verilog code wrappers
#-------------------------------------------
def always_at_posedge( stmt='begin', _clk='' ):
    if _clk == '': _clk = clk
    P( f'always @( posedge {_clk} ) {stmt}' )

#-------------------------------------------
# Replicate expression cnt times as a concatenation
#-------------------------------------------
def repl( expr, cnt ):
    return f'{{{cnt}{{{expr}}}}}'

#-------------------------------------------
# Changed expression width from w to r_w.
# Pad or truncate.
#-------------------------------------------
def resize( expr, w, r_w ):
    if r_w == w: return expr
    if r_w < w:  return f'{expr}[{r_w-1}:0]' 
    return f'{{{r_w-w}\'d0,{expr}}}'

#-------------------------------------------
# Reverse bits (wires only)
#-------------------------------------------
def reverse( bits, w, rbits='' ):
    if rbits == '': rbits = f'{bits}_rev' 
    P(f'reg [{w-1}:0] {rbits};' )
    i = f'{rbits}_i'
    P(f'integer {i}; always @(*) for( {i} = 0; {i} < {w}; {i} = {i} + 1 ) {rbits}[{i}] = {bits}[{w-1}-{i}]; // reverses bits; generates no logic' )
    return rbits

#-------------------------------------------
# Concatenate expressions with width w stored in an array.
# Optionally generate a wire assignment.
# By default, concatenate in reverse order, 
# which is common for eligible masks (vals[0] needs to be the LSB).
#-------------------------------------------
def concata( vals, w, r='', reverse=True ):
    expr = ''
    for v in vals:
        if reverse:
            if expr != '': expr = ', ' + expr
            expr = v + expr
        else:
            if expr != '': expr += ', '
            expr += v
    expr = f'{{{expr}}}' if len(vals) > 1 else expr
    if r != '': wirea( r, w*len(vals), expr )
    return expr

#-------------------------------------------
# Un-concatenate a single signal (bus) into a bunch of sub values.
# Optionally generates multiple wire assignments.
# By default, unconcatenates in reverse order (i.e., LSBs are vals[0])
#-------------------------------------------
def unconcata( combined, cnt, w, r='', reverse=True ):
    vals = []
    for i in range(cnt):
        ii = i if reverse else cnt-1-i
        lsb = i*w
        msb = lsb+w-1
        v = combined if cnt == 1 else f'{combined}[{msb}:{lsb}]'
        vals.append( v )
        if r != '': wirea( f'{r}{i}', w, v )
    return vals

def iface_width( sigs ):
    w = 0
    for sig in sigs:
        w += sigs[sig]
    return w

def iface_decl( kind, name, sigs, is_io=False, stallable=True ):
    if is_io:
        io.append( { 'name': '', 'kind': '', 'width': 0 } )
        if stallable:
            rkind = 'output' if kind == 'input' else 'input' if kind == 'output' else kind
            decl( rkind, name + '_prdy', 1, True )
        decl( kind, name + '_pvld', 1, True )
    for sig in sigs:
        w = sigs[sig]
        decl( kind, name + '_' + sig, w, is_io )
     
def iface_input( name, sigs, stallable=True ):
    iface_decl( 'input', name, sigs, True, stallable )

def iface_output( name, sigs, stallable=True ):
    iface_decl( 'output', name, sigs, True, stallable )

def iface_wire( name, sigs, is_io=False, stallable=True ):
    P()
    if is_io:
        if stallable: decl( 'wire', name + '_prdy', 1, False )
        decl( 'wire', name + '_pvld', 1, False )
    iface_decl( 'wire', name, sigs, False, stallable )

def iface_reg( name, sigs, is_io=False, stallable=True ):
    P()
    if is_io:
        if stallable: decl( 'reg', name + '_prdy', 1, False )
        decl( 'reg', name + '_pvld', 1, False )
    iface_decl( 'reg', name, sigs, False, stallable )

def iface_reg_assign( lname, rname, sigs, indent='        ' ):
    for sig in sigs:
        P(f'{indent}{lname}_{sig} <= {rname}_{sig};' )

def iface_inst( pname, wname, sigs, is_io=False, stallable=True ):
    s = '    '
    if is_io:
        if stallable:
            s += f', .{pname}_prdy({wname}_prdy)'
        s += f', .{pname}_pvld({wname}_pvld)'
    for sig in sigs:
        s += f', .{pname}_{sig}({wname}_{sig})'
    P( s )

def iface_concat( iname, sigs, r='', reverse=True ):
    if len(sigs) == 0: S.die( 'iface_concat: empty sigs list' )
    concat = ''
    w = 0
    for sig in sigs:
        isig = sig if iname == '' else f'{iname}_{sig}'
        w += sigs[sig]
        if reverse:
            if concat != '': concat = ',' + concat
            concat = isig + concat
        else:
            if concat != '': concat += ','
            concat += isig
    if len(sigs) != 1:
        concat = f'{{{concat}}}'
    if r != '':
        wirea( r, w, concat )
        return r
    else:
        return concat

def iface_unconcat( cname, sigs, oname='', reverse=True ):
    if len(sigs) == 0: S.die( 'iface_unconcat: empty sigs list' )
    w = 0
    for sig in sigs: w += sigs[sig]
    lsb = 0
    msb = w - 1
    osigs = {}
    for sig in sigs: 
        sw = sigs[sig]
        if reverse:
            msb = lsb + sw -1 
        else:
            lsb = msb - sw + 1
        v = f'{cname}[{msb}:{lsb}]'
        osigs[sig] = v
        if oname != '': wirea( f'{oname}_{sig}', sw, v )
        if reverse:
            lsb += sw
        else:
            msb = lsb - 1
    return osigs

def iface_combine( iname, oname, sigs, reverse=True, do_decl=True ):
    if do_decl: wire( oname, iface_width(sigs) )
    iconcat = iface_concat( iname, sigs, '', reverse )
    assign = 'assign ' if do_decl else '    '
    P(f'{assign}{oname} = {iconcat};' )

def iface_split( iname, oname, sigs, reverse=True, do_decl=True ):
    if do_decl: iface_wire( oname, sigs )
    oconcat = iface_concat( oname, sigs, '', reverse )
    assign = 'assign ' if do_decl else '    '
    P(f'{assign}{oconcat} = {iname};' )

def iface_stage( iname, oname, sigs, pvld, prdy='', full_handshake=False, do_dprint=True ):
    if prdy == '' or not full_handshake:
        #-----------------------------------------
        # sample - one set of flops
        #-----------------------------------------
        if pvld != '': reg( f'{oname}_{pvld}', 1 )
        if prdy != '': P(f'assign {iname}_{prdy} = !{oname}_pvld || {oname}_{prdy};' )
        for sig in sigs:
            reg( f'{oname}_{sig}', sigs[sig] )
        always_at_posedge()
        if pvld != '':
            P(f'    if ( !{reset_} ) begin' )
            P(f'        {oname}_{pvld} <= 0;' )
            if prdy == '':
                P(f'    end else begin' )
            else:
                P(f'    end else if ( !{oname}_{pvld} || {oname}_{prdy} ) begin' )
            P(f'        {oname}_{pvld} <= {iname}_{pvld};' )
            P(f'        if ( {iname}_{pvld} ) begin' )
            for sig in sigs:
                P(f'            {oname}_{sig} <= {iname}_{sig};' )
            P(f'        end' )
            P(f'    end' )
        else:
            for sig in sigs:
                P(f'    {oname}_{sig} <= {iname}_{sig};' )
        P(f'end' )
        if do_dprint and pvld != '': iface_dprint( iname, sigs, f'{iname}_{pvld}' )
    else:
        #-----------------------------------------
        # full handshake - two sets of flops
        #-----------------------------------------
        P(f'reg {oname}_pvld;    ' )
        P(f'reg {oname}_pvld_n;' )
        iface_reg( f'{oname}__0', sigs )
        iface_reg( f'{oname}__1', sigs )
        P(f'reg {oname}_rd_0;' )
        for sig in sigs: wirea( f'{oname}_{sig}', sigs[sig], f'{oname}_rd_0 ? {oname}__0_{sig} : {oname}__1_{sig}' )
        P()
        P(f'assign {iname}_prdy = !({oname}_pvld && {oname}_pvld_n);' )
        P()
        P(f'wire {oname}_wr_0 = {iname}_pvld && ({iname}_prdy && ({oname}_pvld ? !{oname}_rd_0 :  {oname}_rd_0));' )
        P(f'wire {oname}_wr_1 = {iname}_pvld && ({iname}_prdy && ({oname}_pvld ?  {oname}_rd_0 : !{oname}_rd_0));' )
        P()
        always_at_posedge()
        P(f'    if ( !{reset_} ) begin' )
        P(f'        {oname}_pvld   <= 1\'b0;' )
        P(f'        {oname}_pvld_n <= 1\'b0;' )
        P(f'        {oname}_rd_0   <= 1\'b0;' )
        P(f'    end else begin' )
        P(f'        {oname}_pvld   <= ({iname}_pvld && {iname}_prdy) || ({oname}_pvld && !{oname}_prdy) || {oname}_pvld_n;' )
        P(f'        {oname}_pvld_n <= ({iname}_pvld && {iname}_prdy && {oname}_pvld && !{oname}_prdy) || ({oname}_pvld_n && !{oname}_prdy);' )
        P(f'        {oname}_rd_0   <= ({oname}_pvld && {oname}_prdy) ? !{oname}_rd_0 : {oname}_rd_0;' )
        P(f'    end' )
        P(f'end' )
        P()
        always_at_posedge()
        P(f'    if ( {oname}_wr_0 ) begin' )
        iface_reg_assign( f'{oname}__0', f'{iname}', sigs )
        P(f'    end else begin' )
        P(f'    end' )
        P()
        P(f'    if ( {oname}_wr_1 ) begin' )
        iface_reg_assign( f'{oname}__1', f'{iname}', sigs )
        P(f'    end else begin' )
        P(f'    end' )
        P(f'end' )
        if do_dprint: iface_dprint( iname, sigs, f'{iname}_{pvld}', f'{iname}_prdy' )

def iface_stageN( p, sigs, pvld, prdy='', full_handshake=False, do_print=False ):
    iface_stage( f'p{p}', f'p{p+1}', sigs, pvld, prdy, full_handshake, do_print )

def iface_dprint( name, sigs, pvld, prdy='', use_hex_w=16, with_clk=True, indent='' ):
    isigs = {}
    for sig in sigs: isigs[f'{name}_{sig}'] = sigs[sig]
    vld = pvld
    if prdy != '': vld += f' && {prdy}'
    dprint( name, isigs, vld, use_hex_w=16, with_clk=with_clk, indent=indent )

#---------------------------------------------------------
# wrapped add and sub (combinational)
#
# (A + B) % C
# (A - B) % C
#
# We assume that A and B are unsigned and already < 
# C is a constant.
#---------------------------------------------------------
def wrapped_add( r, w, a, b, c ):
    if is_pow2( c ):
        P(f'wire [{w-1}:0] {r} = {a} + {b};' )
    else:
        P(f'wire [{w}:0] {r}_add = {a} + {b};' )
        P(f'wire [{w-1}:0] {r} = (({r}_add >= {c}) ? ({r}_add - {c}) : {r}_add;' )
    return r

def wrapped_sub( r, w, a, b, c ):
    if is_pow2( c ):
        P(f'wire [{w-1}:0] {r} = {a} - {b};' )
    else:
        P(f'wire [{w}:0] {r}_sub = {a} - {b};' )
        P(f'wire [{w-1}:0] {r} = (({r}_sub >= {c}) ? ({r}_sub + {c}) : {r}_sub;' )
    return r

#---------------------------------------------------------
# adder and subtractor are register values that can wrap
#---------------------------------------------------------
def adder( r, c, do_incr, init=0, incr=1, _clk='', _reset_='' ):
    if _clk == '': _clk = clk
    if _reset_ == '': _reset_ = reset_
    w = log2( c )
    reg( r, w )
    wrapped_add( f'{r}_p', w, r, incr, c )
    always_at_posedge( _clk )
    P(f'    if ( !{_reset_} ) begin' )
    P(f'        {r} <= {init};' )
    P(f'    end else if ( {do_incr} ) begin' )
    P(f'        {r} <= {r}_p;' )
    P(f'    end' )
    P(f'end' )

def subtractor( r, c, do_decr, init=0, decr=1, _clk='', _reset_='' ):
    if _clk == '': _clk = clk
    if _reset_ == '': _reset_ = reset_
    w = log2( c )
    reg( r, w )
    wrapped_sub( f'{r}_p', w, r, decr, c )
    always_at_posedge( _clk )
    P(f'    if ( !{_reset_} ) begin' )
    P(f'        {r} <= {i};' )
    P(f'    end else if ( {do_decr} ) begin' )
    P(f'        {r} <= {r}_p;' )
    P(f'    end' )
    P(f'end' )

#---------------------------------------------------------
# carry lookahead adder 
#---------------------------------------------------------
def cla( r, w, a, b, cin ):
    if not custom_cla: 
        # Let Synopsys do it.
        #
        P(f'wire [{w-1}:0] {r}_S = {a} + {b} + {cin};' )
        return f'{r}_S'
        
    #
    # Custom CLA
    #
    # In this case, we don't rely on sympy to simplify.
    # Instead, we make our own tree of 2-bit CLAs, each
    # taking in two P/G bits from the previous stage.
    #
    # In stage 0, we compute n leaf P and G bits using A and B.
    #     s0_P0 = A0 ^ B0
    #     s0_G0 = A0 | B0
    #     s0_P1 = A1 ^ B1
    #     s0_G1 = A1 | B1
    #     ...
    #
    # In stage 1, we compute n/2 group P and G bits:
    #     s1_P1 = s0_P0 & s0_P1
    #     s1_G1 = s0_G1 | (s0_G0 & s0_P1)       
    #     s1_P3 = s0_P2 & s0_P3
    #     s1_G3 = s0_G3 | (s0_G2 & s0_P3)
    #     ...
    #
    # In stage 2, we compute n/4 group P and G bits:
    #     s2_P3 = s1_P1 & s1_P3
    #     s2_G3 = s1_G3 | (s1_G1 & s1_P3)
    #     s2_P7 = s1_P5 & s1_P7
    #     s2_G7 = s1_G7 | (s1_G5 & s1_P7)
    #     ...
    # 
    # And so forth.
    #     
    # Next, we compute each carry out using the "highest" expression we have:
    #     C0 = CIN
    #     C1 = s0_G0 | (C0 & s0_P0)
    #     C2 = s1_G1 | (C0 & s1_P1)
    #     C3 = s0_G2 | (C2 & s0_P2)
    #     C4 = s2_G3 | (C3 & s2_P3)
    #     C5 = s0_G4 | (C4 & s0_P4)
    #     C6 = s1_G5 | (C5 & s1_P5)
    #     C7 = s0_G6 | (C6 & s0_P0)
    #     C8 = s3_G7 | (C7 & s3_P7)
    #     ...
    #
    # Finally we compute the S bits for the resolved sum.  Straightforward.
    #     S0 = C0 ^ s0_P0
    #     S1 = C1 ^ s0_P1
    #     S2 = C2 ^ s0_P2
    #     ...
    #
    h = {}    # highest stage available for this index

    # stage 0 P/G bits
    s = 0
    for j in range(w):
        P(f'wire {r}_s{s}_P{j} = {a}[{j}] ^ {b}[{j}];' )
        P(f'wire {r}_s{s}_G{j} = {a}[{j}] & {b}[{j}];' )
        h[j] = 0

    # stage 1,2,... P/G bits
    ww = w
    s = 1
    while ww > 1:
        j0 = (1 << (s-1)) - 1
        while j0 < (w-1):
            j1       = j0 + (1 << (s-1))
            s0       = h[j0]
            s1       = h[j1]
            P(f'wire {r}_s{s}_P{j1} = {r}_s{s0}_P{j0} & {r}_s{s0}_P{j1};' )
            P(f'wire {r}_s{s}_G{j1} = {r}_s{s0}_G{j1} | ({r}_s{s0}_G{j0} & {r}_s{s0}_P{j1});' )
            h[j1]    = s
            j0      += 1 << s
        ww = (ww+1) >> 1
        s += 1

    # carry out bits
    P(f'wire ' + r + '_C0 = ' + str(cin) + ';' )
    for j0 in range(w):
        s0 = h[j0]
        P(f'wire {r}_C{j0+1} = {r}_s{s0}_G{j0} | ({r}_C{j0} & {r}_s{s0}_P{j0});' )

    # sum bits
    wire( f'{r}_S', w )
    for j in range(w):
        P(f'assign {r}_S[{j}] = {r}_C{j} ^ {r}_s0_P{j};' )
    return f'{r}_S'

#-------------------------------------------
# compute min/max() in hardware
#-------------------------------------------
def vmin( a, b, r_w, r='' ):
    if r == '': r = f'{a}_min_{b}' 
    wirea( r, r_w, f'({a} <= {b}) ? {a} : {b}' )
    return r

def vmax( a, b, r_w, r='' ):
    if r == '': r = f'{a}_max_{b}' 
    wirea( r, r_w, f'({a} >= {b}) ? {a} : {b}' )
    return r

#-------------------------------------------
# compute integer log2( x ) in hardware
#-------------------------------------------
def vlog2( x, x_w, r='' ):
    if r == '': r = f'{x}_lg2'
    cnt_w = value_bitwidth( x_w )
    ldz = count_leading_zeroes( x, x_w )
    wirea( r, cnt_w, f'{cnt_w}\'d{x_w-1} - {ldz}' )
    return r
    
#-------------------------------------------
# hash a bunch of bits x (width: x_w) down to r_w bits;
# currently this is done by XOR'ing groups of r_w bits with one another,
# but other hash function options could be created in the future
#-------------------------------------------
def hash( x, x_w, r_w, r='' ):
    if r == '': r = f'{x}_hash'
    if r_w == 0:
        expr = '0'
    else:
        groups = []
        lsb = 0
        while lsb < x_w:        
            msb = min( x_w-1, lsb+r_w-1 )
            w = msb - lsb + 1
            groups.append( resize( f'{x}[{msb}:{lsb}]', w, r_w ) )
            lsb = msb + 1
        expr = ' ^ '.join( groups )
    wirea( r, r_w, expr )
    return r

#-------------------------------------------
# fixed-point resize
#-------------------------------------------
def fp_resize( fp1, r, is_signed, int1_w, frac1_w, intr_w, fracr_w ):
    lsb1 = 0 if fracr_w >= frac1_w else frac1_w-fracr_w
    msb1 = lsb1 + fracr_w
    msb1 += int1_w-1 if intr_w >= int1_w else intr_w-1
    zeroes = '' if fracr_w <= frac1_w else f',{fracr_w-frac1_w}\'b0'
    signs = ''
    if is_signed:
        if intr_w <= int1_w:
            msb1 += 1
        else:
            signs = f'{{{intr_w-int1_w+1}{{{fp1}[{int1_w+frac1_w}]}}}},'
    expr = '' if zeroes == '' and signs == '' else '{'
    expr += signs
    expr += f'{fp1}[{msb1}:{lsb1}]'
    expr += zeroes
    if zeroes != '' or signs != '': expr += '}'
    wirea( r, int(is_signed)+intr_w+fracr_w, expr )

#-------------------------------------------
# fixed-point left-shift using array of possible discrete lshs with optional resizing
#-------------------------------------------
def fp_lsha( fp1, sel, lshs, r, is_signed, int1_w, frac1_w, intr_w, fracr_w ):
    vals = []
    w1 = int(is_signed) + int1_w + frac1_w
    wr = int(is_signed) + intr_w + fracr_w
    for lsh in lshs:
        if int1_w == intr_w and frac1_w == fracr_w:
            wirea( f'{r}__{lsh}', wr, fp1 if lsh == 0 else f'{fp1} << {lsh}' )
        else:
            wirea( f'{r}__{lsh}_p', w1+lsh, fp1 if lsh == 0 else f'{fp1} << {lsh}' )
            fp_resize( f'{r}__{lsh}_p', f'{r}__{lsh}', is_signed, int1_w+lsh, frac1_w, intr_w, fracr_w )
        vals.append( f'{r}__{lsh}' )
    muxa( r, wr, sel, vals )

#-------------------------------------------
# fixed-point left-shift with optional resizing
#-------------------------------------------
def fp_lsh( fp1, lsh, lsh_max, r, is_signed, int1_w, frac1_w, intr_w, fracr_w ):
    lshs = [i for i in range(lsh_max+1)]  # all possible left-shifts from 0 to lsh_max
    fp_lsha( fp1, lsh, lshs, r, is_signed, int1_w, frac1_w, intr_w, fracr_w )

#-------------------------------------------
# fixed-point multiply with optional resizing and/or left-shift
#-------------------------------------------
def fp_mul( fp1, fp2, r, is_signed, int1_w, frac1_w, int2_w=-1, frac2_w=-1, intr_w=-1, fracr_w=-1, extra_lsh='', extra_lsh_max=0 ):
    if int2_w == -1: int2_w = int1_w
    if frac2_w == -1: frac2_w = frac1_w
    if intr_w == -1: intr_w = int1_w
    if fracr_w == -1: fracr_w = frac1_w
    if is_signed:
        wirea( f'{r}__{fp1}__is_neg', 1, f'{fp1}[{int1_w+frac1_w}]' )
        wirea( f'{r}__{fp2}__is_neg', 1, f'{fp2}[{int2_w+frac2_w}]' )
        wirea( f'{r}__is_neg', 1, f'{r}__{fp1}__is_neg ^ {r}__{fp2}__is_neg' )
        wirea( f'{r}__{fp1}__u', int1_w+frac1_w, f'{r}__{fp1}__is_neg ? (~{fp1} + 1) : {fp1}' )
        wirea( f'{r}__{fp2}__u', int2_w+frac2_w, f'{r}__{fp2}__is_neg ? (~{fp2} + 1) : {fp2}' )
        fp1 = f'{r}__{fp1}__u'
        fp2 = f'{r}__{fp2}__u'
    wirea( f'{r}__raw', int1_w+int2_w+frac1_w+frac2_w, f'{fp1} * {fp2}' )
    __a = '__a' if is_signed else ''
    if extra_lsh == '':
        fp_resize( f'{r}__raw', f'{r}{__a}', False, int1_w+int2_w, frac1_w+frac2_w, intr_w, fracr_w )
    else:
        fp_lsh( f'{r}__raw', extra_lsh, extra_lsh_max, f'{r}{__a}', False, int1_w+int2_w, frac1_w+frac2_w, intr_w, fracr_w )
    if is_signed:
        wirea( r, 1+intr_w+fracr_w, f'{r}__is_neg ? {{1\'b1, ~{r}__a + {intr_w+fracr_w}\'d1}} : {{1\'b0, {r}__a}}' )

#-------------------------------------------
# For MUX, values need not be constants
#-------------------------------------------
def muxa( r, w, sel, vals, add_reg=True ):
    sw = log2( len(vals) )
    if len(vals) == 1:
        if add_reg:
            wirea( r, w, vals[0] )
        else:
            P( f'always @( * ) {r} = {vals[i]};' )
    elif len(vals) == 2:
        expr = f'{sel} ? {vals[1]} : {vals[0]}'
        if add_reg:
            wirea( r, w, expr )
        else:
            P( f'assign {r} = {expr};' )  
    else:
        if add_reg: P(f'reg [{w-1}:0] {r};' )
        P(f'always @( * ) begin' )
        P(f'    case( {sel} )' )
        for i in range(len(vals)):
            P(f'        {sw}\'d{i}: {r} = {vals[i]};' )
        P(f'        default: {r} = {w}\'d0;' )
        P(f'    endcase' )
        P(f'end' )
    return r

def muxr( r, w, sel, add_reg, *vals ):
    return muxa( r, w, sel, vals, add_reg )

def mux( r, w, sel, *vals ):
    return muxa( r, w, sel, vals )

#-------------------------------------------
# MUX_SUBWORD
#
# If stride is 0, stride is set to subword_w
#
# Subword 0 starts at lsb which defaults to 0.
#-------------------------------------------
def mux_subword( r, subword_w, sel, word, word_w, stride=0, lsb=0, add_reg=True ):
    if stride == 0: stride = subword_w
    vals = []
    while lsb < word_w:
        msb = lsb + subword_w - 1
        if msb >= word_w: msb = word_w - 1
        vals.append( f'{word}[{msb}:{lsb}]' )
        lsb += stride
    return muxr( r, subword_w, sel, add_reg, *vals )

#-------------------------------------------
# MUXN, multiple signals and sets of values are supported
#-------------------------------------------
def muxN( sigs, sel, vals, add_reg=True ):
    sw = log2( len(vals) )
    if add_reg:
        for sig in sigs:
            w = sigs[sig]
            P(f'reg [{w-1}:0] {sig};' )
        P(f'always @( * ) begin' )
    P(f'    case( {sel} )' )
    for i in range(len(vals)):
        P(f'        {sw}\'d{i}: begin' )
        j = 0
        for sig in sigs:
            P(f'            {sig} = {vals[i][j]};' )
            j += 1
        P(f'            end' )
    P(f'        default: begin' )
    for sig in sigs:
        P(f'            {sig} = 0;' )
    P(f'            end' )
    P(f'    endcase' )
    if add_reg:
        P(f'end' )

#-------------------------------------------
# rotate bits left or right by N*w (useful for round-robin scheduling)
#-------------------------------------------
def rotate_left( r, cnt, n, bits, w=1 ):
    tw = cnt*w
    vals = []
    for i in range( cnt ):
        vals.append( bits if i == 0 else f'{{{bits}[{tw-i*w-1}:0], {bits}[{tw-1}:{tw-i*w}]}}' )
    return muxa( r, tw, n, vals )

def rotate_right( r, cnt, n, bits, w=1 ):
    tw = cnt*w
    vals = []
    for i in range( cnt ):
        vals.append( bits if i == 0 else f'{{{bits}[{i*w-1}:0], {bits}[{tw-1}:{i*w}]}}' )
    return muxa( r, tw, n, vals )

#-------------------------------------------
# count zeroes/ones
#-------------------------------------------
def count_zeroes( x, x_w, r='' ):
    sum = ""
    sum_w = log2(x_w+1)
    for i in range( x_w ):
        if i != 0: sum += ' + '
        sum += resize( f'!{x}[{i}]', 1, sum_w )
    if r != '': wirea( r, sum_w, sum )
    return f'({sum})'

def count_ones( x, x_w, r='' ):
    sum = ""
    for i in range( x_w ):
        if i != 0: sum += ' + '
        sum += f'{x}[{i}]'
    if r != '': wirea( r, log2(x_w+1), sum )
    return f'({sum})'

#-------------------------------------------
# count leading zeroes/ones using priority encoder
#-------------------------------------------
def count_leading_zeroes( x, x_w, add_reg=True, suff='_ldz' ):
    cnt_w = value_bitwidth( x_w )
    if add_reg: 
        P( f'// {vlint_off_unused}' )
        reg( f'{x}{suff}', cnt_w )
        P( f'// {vlint_on_unused}' )
    P(f'always @( {x} ) begin' )
    P(f'    casez( {x} )' )
    for i in range( x_w+1 ):
        case = f'{x_w}\'b'
        for k in range( i ): case += '0'
        if i != x_w: case += '1'
        for k in range( i+1, x_w ): case += '?'
        P(f'        {case}: {x}{suff} = {i};' )
    P(f'        default: {x}{suff} = 0;' )
    P(f'    endcase' )        
    P(f'end' )
    return f'{x}{suff}' 

def count_leading_ones( x, x_w, add_reg=True, suff='_ldo' ):
    cnt_w = value_bitwidth( x_w )
    if add_reg: 
        P( f'// {vlint_off_unused}' )
        reg( f'{x}{suff}', cnt_w )
        P( f'// {vlint_on_unused}' )
    P(f'always @( {x} ) begin' )
    P(f'    casez( {x} )' )
    for i in range( x_w+1 ):
        case = f'{x_w}\'b'
        for k in range( i ): case += '1'
        if i != x_w: case += '0'
        for k in range( i+1, x_w ): case += '?'
        P(f'        {case}: {x}{suff} = {i};' )
    P(f'        default: {x}{suff} = 0;' )
    P(f'    endcase' )        
    P(f'end' )
    return f'{x}{suff}' 

#-------------------------------------------
# count trailing zeroes/ones using reverse() and previous 
#-------------------------------------------
def count_trailing_zeroes( x, x_w, add_reg=True, suff='_trz' ):
    reverse( x, x_w, f'{x}_rev' )
    count_leading_zeroes( f'{x}_rev', x_w )
    cnt_w = value_bitwidth( x_w )
    if add_reg: 
        P( f'// {vlint_off_unused}' )
        reg( f'{x}{suff}', cnt_w )
        P( f'// {vlint_on_unused}' )
    P(f'always @( {x}_rev ) {x}{suff} = {x}_rev_ldz;' )
    return f'{x}{suff}' 

def count_trailing_ones( x, x_w, add_reg=True, suff='_ldo' ):
    reverse( x, x_w, f'{x}_rev' )
    count_leading_ones( f'{x}_rev', x_w )
    cnt_w = value_bitwidth( x_w )
    if add_reg: 
        P( f'// {vlint_off_unused}' )
        reg( f'{x}{suff}', cnt_w )
        P( f'// {vlint_on_unused}' )
    P(f'always @( {x}_rev ) {x}{suff} = {x}_rev_ldz;' )
    return f'{x}{suff}' 

#-------------------------------------------
# find first one after/before position i
# after:  ROR by i+1, then use count_trailing_zeroes()
# before: ROR by i+0, then use count_leading_zeroes()
# currently x_w must be a power of 2
#-------------------------------------------
def first_one_after_i( x, x_w, i, r ):
    if not is_pow2( x_w ): die( f'first_one_after_i: x_w must be a power-of-2 right now' )
    ror_w = log2( x_w )
    wirea( f'{i}_p1', ror_w, f'{i} + 1' )
    rotate_right( f'{x}_ror', x_w, f'{i}_p1', x )
    count_trailing_zeroes( f'{x}_ror', x_w )
    wirea( r, ror_w, f'{x}_ror_trz + {i}_p1' )
    return r

def first_one_before_i( x, x_w, i, r ):
    if not is_pow2( x_w ): die( f'first_one_before_i: x_w must be a power-of-2 right now' )
    ror_w = log2( x_w )
    rotate_right( f'{x}_ror', x_w, i, x )
    count_leading_zeroes( f'{x}_ror', x_w )
    wirea( r, ror_w, f'{x}_ror_ldz + {i}' )
    return r

#-------------------------------------------
# determine if a one_hot mask is really a one-hot mask
# there should be at most one bit set
#-------------------------------------------
def is_one_hot( mask, mask_w, r='' ):
    ioh = count_ones( mask, mask_w ) + ' <= 1'
    if r != '': wirea( r, 1, ioh )
    return ioh

#-------------------------------------------
# get a one-hot mask from a binary value     
# by default, it returns an expression but can also declare a wire
# if pvld is supplied, it will not set the bit unless pvld is 1
#-------------------------------------------
def binary_to_one_hot( b, mask_w, r='', pvld='' ):
    mask = f'{mask_w}\'d1 << {b}'
    if pvld != '': mask = f'({mask}) & ' + repl( pvld, mask_w )
    if r != '': wirea( r, mask_w, mask )

#-------------------------------------------
# get index of 1 bit in one-hot mask
# optionally sets "any_vld" flag if any bit is set
# assumes: at most one bit is set, so can use an OR tree
#-------------------------------------------
def one_hot_to_binary( mask, mask_w, r, r_any_vld='' ):
    r_w = log2( mask_w )
    expr = ''
    for i in range(mask_w):
        if i != 0: expr += ' | '
        expr += f'({mask}[{i}] ? {i} : 0)'
    wirea( r, r_w, expr )
    if r_any_vld != '': wirea( r_any_vld, 1, f'|{mask}' )
    dassert( is_one_hot( mask, mask_w ), f'{mask} should have no bits set or exactly one bit set' )

#-------------------------------------------
# Collapse 1 bits from a mask.
# For example, if the mask is 4'b1010, the result will be 4'0011.
# If gen_indexes is True (default), then we also produce a collapsed set of 
# mask indexes, such as {xxx, xxx, 2'd3, 2'd1} in this example, which 
# will be needed if you decide to use uncollapse() below.
# Further you may supply other sets of values to get collapsed using
# a dictionary, such as the following 32-bit addr and 4-bit x values:
#      vals = { 'addr': [ 32, '{addr3, addr2, addr1, addr0}' ],
#               'x':    [  4, '{x3, x2, x1, x0}' ] }
# then results will be (in this example):
#      {r}_vlds    = 4'b0011
#      {r}_indexes = {xxx, xxx,  2'd3,  2'd1}
#      {r}_addr    = {xxx, xxx, addr3, addr1} 
#      {r}_x       = {xxx, xxx,    x3,    x1}
#
# You can use concata() to take a list of values and concatenate them into 
# the single signal such as the ones shown.
# 
# You can also use unconcata() to take a single bus and split it into 
# multiple signals.
#-------------------------------------------
def collapse( mask, mask_w, r, vals={}, gen_indexes=True ):
    _vals = {}
    for val in vals:
        w = vals[val][0]
        s = vals[val][1]
        _vals[val] = [w, []]
        for i in range(mask_w):
            lsb = i*w
            msb = lsb + w - 1
            v = s if mask_w == 1 else f'{mask}[{i}] ? {s}[{msb}:{lsb}] : {w}\'d0'
            _vals[val][1].append( v )

    if 'vlds' in vals: S.die( f':collapse: {r} vals may not have an entry called "vlds"' )
    _vals['vlds'] = [ 1, [] ]
    for i in range(mask_w):
        v = mask if mask_w == 1 else f'{mask}[{i}]' 
        _vals['vlds'][1].append( v )
    if gen_indexes:
        if 'indexes' in vals: S.die( f'collapse: {r} gen_indexes=True is allowed only if there is no "indexes" in vals={vals}' )
        index_w = max( 1, log2( mask_w ) )
        _vals['indexes'] = [ index_w, [] ]
        for i in range(mask_w):
            v = '1\'d0' if mask_w == 1 else f'{mask}[{i}] ? {index_w}\'d{i} : {index_w}\'d0'
            _vals['indexes'][1].append( v )

    vld_cnts = _vals['vlds'][1].copy()
    vld_cnt_w = 1
    i = 0
    cnt = mask_w
    while cnt > 1: 
        vld_cnt_max = (1 << vld_cnt_w) - 1
        new_vld_cnts = []
        new_vals = {}
        for val in _vals: 
            new_vals[val] = [ _vals[val][0], [] ]
        for j in range((cnt+1) >> 1):
            i0 = j*2 + 0
            i1 = j*2 + 1
            if i1 < cnt:
                new_vld_cnt = f'{r}_vld_cnt_{i}_{j}'
                wirea( new_vld_cnt, vld_cnt_w+1, f'{vld_cnts[i0]} + {vld_cnts[i1]}' )
                new_vld_cnts.append( new_vld_cnt )
                for val in _vals:
                    w = _vals[val][0]
                    opnd0 = _vals[val][1][i0]
                    opnd1 = _vals[val][1][i1]
                    w_times = f'{w}*' if w > 1 else ''
                    expr  = f'{opnd0} | ({opnd1} << ({w_times}{vld_cnts[i0]}))'
                    wirea( f'{r}_{val}_{i}_{j}', w*(vld_cnt_max+1), expr )
                    new_vals[val][1].append( f'{r}_{val}_{i}_{j}' )
            else:
                new_vld_cnts.append( vld_cnts[i0] )
                for val in _vals:
                    new_vals[val][1].append( _vals[val][1][i0] )
        vld_cnts = new_vld_cnts
        _vals = new_vals
        i += 1
        cnt = len( vld_cnts )
        vld_cnt_w += 1
    for val in _vals:
        w = _vals[val][0]
        wirea(f'{r}_{val}', mask_w*w, _vals[val][1][0] )

#-------------------------------------------
# Un-collapse previous collapsed values using the collapsed mask and mask indexes.
# For example, say we have mask_indexes = {xx, xx, 2'd3, 2'd1} and we want to uncollapse:
#      vals = { 'addr': [32, '{xxx, xxx, addr3, addr1}' ]
#                'x':   [ 4, '{xxx, xxx,    x3,    x1}' ] }
# then results will be (in this example):
#      {r}_addr = {addr3, xxx, addr1, xxx}
#      {r}_x    = {   x3, xxx,   x1,  xxx}
#
# It is up to the caller to not look at sub-values that can't be valid.
# That usually means looking at the pre-collapsed mask (4'b1010 in this example).
#
# See prior comments about concata() and unconcata().
#-------------------------------------------
def uncollapse( mask, indexes, index_cnt, vals, r ):
    index_w = max( 1, log2(index_cnt) )
    results = []
    for val in vals:
        w = vals[val][0]
        sig = vals[val][1]
        vr = ''
        for i in range(index_cnt):
            lsb = i*w
            msb = lsb + w - 1
            ilsb = i*index_w
            imsb = ilsb + index_w - 1
            idx = indexes if index_cnt == 1 else f'{indexes}[{imsb}:{ilsb}]'
            v = sig if index_cnt == 1 else f'{sig}[{msb}:{lsb}]'
            if i != 0: vr += f' | '
            vr += v if index_cnt == 1 else f'({mask}[{i}] ? ({v} << ({idx}*{w})) : 0)'
        results.append( vr )    
        if r != '': wirea( f'{r}_{val}', index_cnt*w, vr )
    return results

#-------------------------------------------
# choose eligible from mask and preferred 
#
# note: elig_mask should be right-to-left order
#-------------------------------------------
def choose_eligible( r, elig_mask, cnt, preferred, gen_preferred=False, adv_preferred='' ):
    if cnt <= 0: S.die( f'choose_eligible: cnt is {cnt}' )
    if cnt == 1:
        # trivial case
        wirea( f'{elig_mask}_any_vld', 1, f'{elig_mask}' )
        wirea( r, 1, '1\'d0' )
        return r

    # cnt > 1
    w = log2( cnt )
    if gen_preferred: reg( preferred, w )
    reverse( elig_mask, cnt, f'{elig_mask}_r' )
    prio_elig_mask = rotate_left( f'{r}_prio_elig_mask', cnt, preferred, f'{elig_mask}_r' )
    choice = count_leading_zeroes( prio_elig_mask, cnt )
    P( f'// {vlint_off_width}' )
    if is_pow2( cnt ):
        wirea( r, w, f'{preferred} + {choice}' )
    else:
        wirea( f'{r}_p', w+1, f'{preferred} + {choice}' )
        wirea( r, w, f'({r}_p >= {cnt}) ? ({r}_p - {cnt}) : {r}_p' )
    P( f'// {vlint_on_width}' )
    wirea( f'{elig_mask}_any_vld', 1, f'|{elig_mask}' )
    if gen_preferred:
        always_at_posedge()
        P(f'    if ( !{reset_} ) begin' )
        P(f'        {preferred} <= 0;' )
        if adv_preferred: adv_preferred = f' && {adv_preferred}'
        P(f'    end else if ( {elig_mask}_any_vld{adv_preferred} ) begin' )
        P(f'        {preferred} <= {r} + 1;' )
        P(f'    end' )
        P(f'end' )
    return r

#-------------------------------------------
# choose eligible from mask with highest priority
# using a binary search
#-------------------------------------------
def choose_eligible_with_highest_prio( r, vlds, prios, prio_w ):
    P()
    cnt     = len(vlds)
    choice_w = log2(cnt) if cnt > 1 else 1
    choices = [i for i in range(cnt)]
    i = 0
    P( f'// {vlint_off_unused}' )
    while cnt > 1: 
        new_vlds    = []
        new_prios   = []
        new_choices = []
        depth = (cnt+1) >> 1
        for j in range(depth):
            i0 = j*2 + 0
            i1 = j*2 + 1
            if i1 < cnt:
                vld  = f'{r}_vld_{i}_{j}'
                prio = f'{r}_prio_{i}_{j}'
                which = f'{r}_which_{i}_{j}'
                choice = f'{r}_choice_{i}_{j}'
                wirea( vld, 1, f'{vlds[i0]} || {vlds[i1]}' )
                wirea( which, 1, f'!{vlds[i0]} || ({vlds[i1]} && {prios[i1]} > {prios[i0]})' )
                wirea( prio, prio_w, f'{which} ? {prios[i1]} : {prios[i0]}' )
                wirea( choice, choice_w, f'{which} ? {choices[i1]} : {choices[i0]}' )
            else:
                vld  = vlds[i0]
                prio = prios[i0]
                choice = choices[i0]
            new_vlds.append( vld )    
            new_prios.append( prio )    
            new_choices.append( choice )    
        vlds = new_vlds
        prios = new_prios
        choices = new_choices
        i += 1
        cnt = len( choices )
    P( f'// {vlint_on_unused}' )
    wirea(f'{r}_vld', 1, vlds[0] )
    cnt = len(vlds)
    wirea(f'{r}_i', choice_w, choices[0] )

#-------------------------------------------
# choose multiple eligibles from elig_mask and 
# assign them to requestors from req_mask.
#
# results:
#     {r}_elig_vlds        is a mask of all eligibles that were successfully assigned
#     {r}_elig_req_indexes holds the indexes of the requestors to which each eligible was assigned (when elig_vlds bit is set)
#     {r}_req_vlds         is a mask of all requestors that were assigned 
#     {r}_req_elig_indexes holds the indexes of the eligibles that were assigned to requestors (when req_vlds bit is set) 
#
# We collapse the eligibles and collapse the requestors, then assign as much as we can.
#-------------------------------------------
def choose_eligibles( r, elig_mask, elig_cnt, preferred, req_mask, req_cnt, gen_preferred=False, adv_preferred='' ):
    if not is_pow2( elig_cnt ): S.die( f'choose_eligibles: elig_cnt={elig_cnt} must be a power-of-2 for now' )
    elig_index_w = max(1, log2(elig_cnt))
    req_index_w  = max(1, log2(req_cnt))
    if gen_preferred: reg( preferred, elig_index_w )
    rotate_right( f'{r}_pelig_mask', elig_cnt, preferred, elig_mask )
    collapse( f'{r}_pelig_mask', elig_cnt, f'{r}_collapsed_pelig' )
    collapse( req_mask,          req_cnt,  f'{r}_collapsed_req' )
    used_w = min( elig_cnt, req_cnt )
    wirea( f'{r}_collapsed_used', used_w, f'{r}_collapsed_pelig_vlds & {r}_collapsed_req_vlds' )
    wirea( f'{r}_collapsed_pelig_used', elig_cnt, f'{r}_collapsed_used' )
    wirea( f'{r}_collapsed_pelig_req_indexes', elig_cnt*req_index_w, f'{r}_collapsed_req_indexes' )
    wirea( f'{r}_collapsed_req_used',  req_cnt,  f'{r}_collapsed_used' )
    wirea( f'{r}_collapsed_req_pelig_indexes', req_cnt*elig_index_w, f'{r}_collapsed_pelig_indexes' )
    uncollapse( f'{r}_collapsed_pelig_vlds', f'{r}_collapsed_pelig_indexes', elig_cnt, { 'vlds':          [1,            f'{r}_collapsed_pelig_used'] },        f'{r}_pelig' )
    uncollapse( f'{r}_collapsed_pelig_vlds', f'{r}_collapsed_pelig_indexes', elig_cnt, { 'req_indexes':   [req_index_w,  f'{r}_collapsed_pelig_req_indexes'] }, f'{r}_pelig' )
    rotate_left( f'{r}_elig_vlds',        elig_cnt, preferred, f'{r}_pelig_vlds' )
    rotate_left( f'{r}_elig_req_indexes', elig_cnt, preferred, f'{r}_pelig_req_indexes', req_index_w )
    uncollapse( f'{r}_collapsed_req_vlds',   f'{r}_collapsed_req_indexes',   req_cnt,  { 'vlds':          [1,            f'{r}_collapsed_req_used'] },          f'{r}_req' )
    uncollapse( f'{r}_collapsed_req_vlds',   f'{r}_collapsed_req_indexes',   req_cnt,  { 'pelig_indexes': [elig_index_w, f'{r}_collapsed_req_pelig_indexes'] }, f'{r}_req' )
    elig_indexes = []
    for i in range(req_cnt):
        lsb = i * elig_index_w
        msb = lsb + elig_index_w - 1
        elig_index = f'{r}_req_pelig_indexes[{msb}:{lsb}] + {preferred}' if i < elig_cnt else f'{elig_index_w}\'d0'
        elig_indexes.append( elig_index )
    concata( elig_indexes, elig_index_w, f'{r}_req_elig_indexes' )
    if gen_preferred:
        always_at_posedge()
        P(f'    if ( !{reset_} ) begin' )
        P(f'        {preferred} <= 0;' )
        if adv_preferred: adv_preferred = f' && {adv_preferred}'
        P(f'    end else if ( |{r}_collapsed_used{adv_preferred} ) begin' )
        P(f'        {preferred} <= {preferred} + 1;' )
        P(f'    end' )
        P(f'end' )

#-------------------------------------------
# resource accounting for <cnt> resource slots
#-------------------------------------------
def resource_accounting( name, cnt, add_free_cnt=False, set_i_is_free_i=False ):
    P()
    id_w = log2(cnt) if cnt > 1 else 1
    reg( f'{name}_in_use', cnt )
    reverse( f'{name}_in_use', cnt, f'{name}_in_use_r' )
    count_leading_ones( f'{name}_in_use_r', cnt )
    wirea( f'{name}_free_pvld', 1, f'!(&{name}_in_use)' )
    wirea( f'{name}_free_i', id_w, f'{name}_in_use_r_ldo[{id_w-1}:0]' )
    if add_free_cnt: count_zeroes( f'{name}_in_use', cnt, f'{name}_free_cnt' )
    wire( f'{name}_set_pvld', 1 )
    if set_i_is_free_i:
        wirea( f'{name}_set_i', id_w, f'{name}_free_i' )
    else:
        wire( f'{name}_set_i', id_w )
    wire( f'{name}_clr_pvld', 1 )
    wire( f'{name}_clr_i', id_w )
    always_at_posedge()
    P(f'    if ( !{reset_} ) begin' )
    P(f'        {name}_in_use <= 0;' )
    P(f'    end else if ( {name}_set_pvld || {name}_clr_pvld ) begin' )
    P(f'        // {vlint_off_width}' )
    P(f'        {name}_in_use <= ({name}_in_use & ~({name}_clr_pvld << {name}_clr_i)) | ({name}_set_pvld << {name}_set_i);' )
    P(f'        // {vlint_on_width}' )
    P(f'    end' )
    P(f'end')

#-------------------------------------------
# For ROM, values must be decimal constants.
# The ROM can return multiple results.
# The maximum number of results to return is figured out automatically.
# The widths of the results are also figured out automatically.
# If values are missing, they are assumed to be 0.
#-------------------------------------------
def rom_1d( i0, names, entries, nesting=0, result_w=None ):
    result_cnt = len( names )
    entry_cnt = len( entries )
    if not isinstance( entries[0], list ): 
        # normalize array
        new_entries = [ [entries[i]] for i in range( entry_cnt ) ]
        entries = new_entries
    i0_w = log2(entry_cnt)
    indent = ''
    for i in range( nesting ): indent += '    '
    if nesting == 0:
        result_max = [ 0 for i in range( result_cnt ) ]
        for entry in entries:
            for i in range( len( entry ) ):
                if entry[i] > result_max[i]: result_max[i] = entry[i]
        result_w = [ value_bitwidth(result_max[i]) for i in range( result_cnt ) ]
        P()
        P(f'// ROM' )
        P(f'//' )
        for i in range( result_cnt ):
            reg( names[i], result_w[i] )
        P(f'always @( * ) begin' )

    P(f'{indent}    case( {i0} )' )
    for e in range( entry_cnt ):
        entry = entries[e]
        if result_cnt == 1:
            v = entry[0] if len( entry ) > 0 else 0
            v = f'{result_w[0]}\'h{{0:x}}'.format( v )
            P(f'{indent}    {i0_w}\'d{e}: {names[0]} = {v};' )
        else:
            P(f'{indent}    {i0_w}\'d{e}: begin' )
            for i in range( result_cnt ):
                v = entry[i] if i < len( entry ) else 0
                v = f'{result_w[i]}\'h{{0:x}}'.format( v )
                P(f'{indent}        {names[i]} = {v};' )
            P(f'{indent}        end' )
    if result_cnt == 1:
        P(f'{indent}    default: {names[0]} = 0;' )
    else: 
        P(f'{indent}    default: begin' )
        for i in range( result_cnt ):
            P(f'{indent}        {names[i]} = 0;' )
        P(f'{indent}        end' )
    P(f'{indent}    endcase' )

    if nesting == 0:
        P(f'end' )

def rom_2d( i0, i1, names, entries, nesting=0, result_w=None ):
    result_cnt = len( names )
    entry_cnt = len( entries )
    if not isinstance( entries[0][0], list ): 
        # normalize array
        new_entries = []
        for i in range( entry_cnt ):
            new_entries.append( [ [entries[i][i1]] for i1 in range( len(entries[i]) ) ] )
        entries = new_entries
    i0_w = log2(entry_cnt)
    indent = ''
    for i in range( nesting ): indent += '    '
    if nesting == 0:
        result_max = [ 0 for i in range( result_cnt ) ]
        for i in range( entry_cnt ):
            for entry in entries[i]:
                for i in range( len( entry ) ):
                    if entry[i] > result_max[i]: result_max[i] = entry[i]
        result_w = [ value_bitwidth(result_max[i]) for i in range( result_cnt ) ]
        P()
        P(f'// ROM' )
        P(f'//' )
        for i in range( result_cnt ):
            reg( names[i], result_w[i] )
        P(f'always @( * ) begin' )

    P(f'{indent}    case( {i0} )' )
    for e in range( entry_cnt ):
        entry = entries[e]
        P(f'{indent}    {i0_w}\'d{e}:' )
        rom_1d( i1, names, entry, nesting+1, result_w )
    P(f'{indent}    default: begin' )
    for i in range( result_cnt ):
        P(f'{indent}        {names[i]} = 0;' )
    P(f'{indent}        end' )
    P(f'{indent}    endcase' )

    if nesting == 0:
        P(f'end' )

#--------------------------------------------------------------------
# By default, this generates a 2-port synchronous ram (1 clock).
#
# wr_cnt, rd_cnt, and rw_cnt can be changed to control the number of read ports, write ports,
# and bi-directional ports. A ram may not have any write or read ports if it has any bi-directional ports.
#
# clks=[...] will cause each port to have its own clock and to use the clocks
# in the list. The number of clocks must match the number of ports. Write clocks must 
# be listed before read clocks.
#
# If you specified an external ram generator using ramgen_cmd=... in reinit(),
# then you must supply an m_name that can be parsed by your proprietary ram
# generator so that it will generate a ram that abides by the expectations
# of other arguments specified here, namely wr_cnt, rd_cnt, and rw_cnt. 
# There are also expectations for ram port names, such as: we, wa, di, re, ra, dout. 
# If these don't match, we could provide other arguments in reinit() to change the names,
# OR you could supply a ramgen_cmd that creates a canonical wrapper around the actual ram.
#--------------------------------------------------------------------
def ram( iname, oname, sigs, depth, wr_cnt=1, rd_cnt=1, rw_cnt=0, clks=[], m_name='', u_name='', add_blank_line=True ):
    port_cnt = wr_cnt + rd_cnt + rw_cnt
    have_clks = len(clks) != 0
    if have_clks and len(clks) != port_cnt: S.die( f'ram(): if clks=[...] is given, the number of clocks must match the number of ports' )
    if port_cnt <= 0: S.die( f'ram(): 0-port ram is not allowed' )
    if (wr_cnt == 0) != (rd_cnt == 0): S.die( f'ram(): if you have a write port, you must have a read port, and vice-versa' )
    if wr_cnt != 0 and rw_cnt != 0: S.dir( f'ram(): you may not have both wr(rd) ports and bi-directional rw ports at the same time' )
    if wr_cnt > 1 or rw_cnt > 1 and iname == '': S.dir( f'ram(): iname must be supplied when wr_cnt > 1 or rw_cnt > 1' )
    if rd_cnt > 1 or rw_cnt > 1 and oname == '': S.dir( f'ram(): oname must be supplied when rd_cnt > 1 or rw_cnt > 1' )

    w = 0
    for sig in sigs: w += sigs[sig]

    if m_name == '': m_name = f'ram_{depth}x{w}_wr{wr_cnt}_rd{_rd_cnt}_rw{rw_cnt}'
    if u_name == '': u_name = f'u_{m_name}'
    rams[m_name] = {'depth': depth, 'w': w, 'wr_cnt': wr_cnt, 'rd_cnt': rd_cnt, 'rw_cnt': rw_cnt, 'ramgen_cmd': ramgen_cmd }

    if add_blank_line: P()
    names = ', '.join( sigs.keys() )
    P(f'// {depth}x{w} {port_cnt}-port ram for: {names}' )
    P(f'//' )

    inst_sigs = '' if have_clks else f'.clk( {clk} )'
    clk_i = 0
    for i in range(wr_cnt):
        wr_name = '' if iname == '' else f'{iname}_'
        suff = '' if wr_cnt == 1 else f'{i}'
        if have_clks: 
            if inst_sigs != '': inst_sigs += ', '
            inst_sigs += f'.clk_w{suff}( {clks[clk_i]} )' 
            clk_i += 1
        inst_sigs += f', .we{suff}( {wr_name}we{suff} )'
        inst_sigs += f', .wa{suff}( {wr_name}wa{suff} )'
        ins = ''
        for sig in sigs:
            if ins != '': ins += ', '
            ins += f'{wr_name}{sig}'
        inst_sigs += f', .di{suff}( {ins} )'
    
    for i in range(rd_cnt):
        rd_name = '' if oname == '' else f'{oname}_'
        suff = '' if rd_cnt == 1 else f'{i}'
        if have_clks: 
            inst_sigs += f', .clk_r{suff}( {clks[clk_i]} )' 
            clk_i += 1
        inst_sigs += f', .re{suff}( {rd_name}re{suff} )'
        inst_sigs += f', .ra{suff}( {rd_name}ra{suff} )'
        outs = ''
        for sig in sigs:
            wire( f'{rd_name}{sig}', sigs[sig] )
            if outs != '': outs += ', '
            outs += f'{rd_name}{sig}'
        inst_sigs += f', .dout{suff}( {outs} )'
    
    for i in range(rw_cnt):
        wr_name = '' if iname == '' else f'{iname}_'
        rd_name = '' if oname == '' else f'{oname}_'
        suff = '' if wr_cnt == 1 else f'{i}'
        if have_clks: 
            if inst_sigs != '': inst_sigs += ', '
            inst_sigs += f', .clk{suff}( {clks[clk_i]} )' 
            clk_i += 1
        inst_sigs += f', .we{suff}( {wr_name}we{suff} )'
        inst_sigs += f', .a{suff}( {wr_name}a{suff} )'
        inst_sigs += f', .re{suff}( {rd_name}re{suff} )'
        ins = ''
        outs = ''
        for sig in sigs:
            wire( f'{rd_name}{sig}', sigs[sig] )
            if ins  != '': ins  += ', '
            if outs != '': outs += ', '
            ins  += f'{wr_name}{sig}'
            outs += f'{rd_name}{sig}'
        inst_sigs += f', .di{suff}( {ins} )'
        inst_sigs += f', .dout{suff}( {outs} )'
    
    P(f'{m_name} {u_name}( {inst_sigs}' )

def make_ram( module_name ):
    info = rams[module_name]
    if ramgen_cmd == '':
        S.die( f'make_ram(): currently cannot generate rams without reinit( ramgen_cmd=... ) being set - restriction will be lifted soon' )
    else:
        P()
        P(f'// {module_name} generated externally using: {ramgen_cmd} {module_name}' )
        P(f'//' )
        S.cmd( f'{ramgen_cmd} {module_name}', echo=False, echo_stdout=False )

def fifo( iname, oname, sigs, pvld, prdy, depth, m_name='', u_name='', with_wr_prdy=True ):
    if depth > 1: depth += 1
    w = 0
    for sig in sigs: w += sigs[sig]

    m_name = f'{module_name}_fifo_{depth}x{w}'
    if u_name == '': u_name = f'u_{m_name}'
    fifos[m_name] = {'depth': depth, 'w': w}

    P()
    names = ', '.join( sigs.keys() )
    P(f'// {depth}x{w} fifo for: {names}' )
    P(f'//' )

    if iname != '': iname += '_' 
    if oname != '': oname += '_' 
    ins = ''
    outs = ''
    wr_pvld = f'{iname}{pvld}'
    wr_prdy = f'{iname}{prdy}'
    rd_pvld = f'{oname}{pvld}'
    rd_prdy = f'{oname}{prdy}'
    if with_wr_prdy: 
        wire( wr_prdy, 1 )
    else:
        wr_prdy = ''
    wire( rd_pvld, 1 )
    wire( rd_prdy, 1 )
    for sig in sigs:
        wire( f'{oname}{sig}', sigs[sig] )
        if ins  != '': ins  += ', '
        if outs != '': outs += ', '
        ins  += f'{iname}{sig}'
        outs += f'{oname}{sig}'
    
    P(f'{m_name} {u_name}( .{clk}({clk}), .{reset_}({reset_}),' )
    P(f'                        .wr_pvld({wr_pvld}), .wr_prdy({wr_prdy}), .wr_pd('+'{'+f'{ins}'+'}),' )
    P(f'                        .rd_pvld({rd_pvld}), .rd_prdy({rd_prdy}), .rd_pd('+'{'+f'{outs}'+'}) );' )
    if with_wr_prdy:
        P(f'// synopsys translate_off' )
        always_at_posedge()
        P(f'    if ( {reset_} === 1 && {wr_pvld} !== 0 && {wr_prdy} !== 1 ) begin' )
        P(f'        $display( "%0d: %m: ERROR: fifo wr_pvld=%d but wr_prdy=%d", $stime, {wr_pvld}, {wr_prdy} );' )
        P(f'        $fatal;' )
        P(f'    end' )
        P(f'end' )
        P(f'// synopsys translate_on' )

def make_fifo( module_name ):
    info = fifos[module_name]
    P()
    P(f'module {module_name}( {clk}, {reset_}, wr_pvld, wr_prdy, wr_pd, rd_pvld, rd_prdy, rd_pd );' )
    P()
    input(  clk,       1 )
    input(  reset_,    1 )
    P()
    input(  'wr_pvld',   1 )
    output( 'wr_prdy',   1 )
    input(  'wr_pd',     info['w'] )
    P()
    output( 'rd_pvld',   1 )
    input(  'rd_prdy',   1 )
    output( 'rd_pd',     info['w'] )
    P()
    depth = info['depth']
    if depth == 0:
        P(f'assign {wr_prdy,rd_pvld,rd_pd} = {rd_prdy,wr_pvld,wr_pd};' )
    elif depth == 1:
        P()
        P(f'// simple flop' )
        P(f'//' )
        reg( 'rd_pvld', 1 )
        reg( 'rd_pd', info['w'] )
        always_at_posedge()
        P(f'    rd_pvld <= wr_pvld;' )
        P(f'    if ( wr_pvld ) rd_pd <= wr_pd;' )
        P(f'end' )
    else:
        w     = info['w']
        a_w   = log2( depth )
        cnt_w = a_w
        cnt_w = (a_w+1) if (1 << a_w) >= depth else a_w
        P(f'// flop ram' )
        P(f'//' )
        for i in range( depth ): reg( f'ram_ff{i}', w )
        P()
        P(f'// PUSH/POP' )
        P(f'//' ) 
        reg( 'cnt', cnt_w )
        P(f'wire wr_pushing = wr_pvld && wr_prdy;' )
        P(f'wire rd_popping = rd_pvld && rd_prdy;' )
        always_at_posedge()
        P(f'    if ( !{reset_} ) begin' )
        P(f'        cnt <= 0;' )
        P(f'    end else if ( wr_pushing != rd_popping ) begin' )
        P(f'        cnt <= cnt + wr_pushing - rd_popping;' )
        P(f'    end' )
        P(f'end' )
        P()
        P(f'// WRITE SIDE' )
        P(f'//' ) 
        reg( 'wr_adr', a_w )
        P(f'assign wr_prdy = cnt != {depth} || rd_popping;' )
        always_at_posedge()
        P(f'    if ( !{reset_} ) begin' )
        P(f'        wr_adr <= 0;' )
        P(f'    end else if ( wr_pushing ) begin' )
        P(f'        case( wr_adr )' )
        for i in range( depth ): P(f'            {a_w}\'d{i}: ram_ff{i} <= wr_pd;' )
        P(f'        endcase' )
        P()
        P(f'        wr_adr <= (wr_adr == {depth-1}) ? 0 : (wr_adr+1);' )
        P(f'    end' )
        P(f'end' )
        P()
        P(f'// READ SIDE' )
        P(f'//' )
        reg( 'rd_adr', a_w )
        always_at_posedge()
        P(f'    if ( !{reset_} ) begin' )
        P(f'        rd_adr <= 0;' )
        P(f'    end else if ( rd_popping ) begin' )
        P(f'        rd_adr <= (rd_adr == {depth-1}) ? 0 : (rd_adr+1);' )
        P(f'    end' )
        P(f'end' )
        P()
        P(f'assign rd_pvld = cnt != 0;' )
        P(f'reg [{w-1}:0] rd_pd_p;' )
        P(f'assign rd_pd = rd_pd_p;' )
        P(f'always @( * ) begin' )
        P(f'    case( rd_adr )' )
        for i in range( depth ): P(f'        {a_w}\'d{i}: rd_pd_p = ram_ff{i};' )
        P(f'        // VCS coverage off' )
        P(f'        default: begin' )
        P(f'            rd_pd_p = {w}\'d0;' )
        P(f'            // synopsys translate_off' )
        P(  '            rd_pd_p = {'+f'{w}'+'{1\'bx}};' )
        P(f'            // synopsys translate_on' )
        P(f'            end' )
        P(f'        // VCS coverage on' )
        P(f'    endcase' )
        P(f'end' )
    P()
    P(f'endmodule // {module_name}' )

def cache_tags( name, addr_w, tag_cnt, req_cnt, ref_cnt_max, incr_ref_cnt_max=1, decr_req_cnt=0, can_always_alloc=False, custom_avails=False ):
    if incr_ref_cnt_max < 1: S.die( f'cache_tags: incr_ref_cnt_max needs to be at least 1' )
    if decr_req_cnt == 0: decr_req_cnt = req_cnt

    P()
    P(f'// {name} cache tags: addr_w={addr_w} tag_cnt={tag_cnt} req_cnt={req_cnt} ref_cnt_max={ref_cnt_max}' )
    P(f'//' )
    tag_i_w = max( 1, log2( tag_cnt ) )
    req_i_w = max( 1, log2( req_cnt ) )
    name_uc = name.upper()
    enum( f'{name_uc}_', ['MISS_CANT_ALLOC', 'MISS', 'HIT', 'HIT_BEING_FILLED'] )
    ref_cnt_w = log2( ref_cnt_max+1 )
    for i in range(tag_cnt): reg( f'{name}__ref_cnt{i}', ref_cnt_w )
    reg( f'{name}__vlds', tag_cnt )
    for i in range(tag_cnt): reg( f'{name}__addr{i}', addr_w )
    reg( f'{name}__filleds', tag_cnt )

    P()
    P(f'// {name} hit checks' )
    P(f'//' )
    hits = ''
    needs_allocs = []
    for r in range(req_cnt):
        wirea( f'{name}_req{r}__hit_one_hot', tag_cnt, concata( [f'{name}_req{r}_pvld && {name}__vlds[{i}] && {name}_req{r}_addr == {name}__addr{i}' for i in range(tag_cnt)], 1 ) )
        one_hot_to_binary( f'{name}_req{r}__hit_one_hot', tag_cnt, f'{name}_req{r}__hit_i', f'{name}_req{r}__hit_vld' )
        wirea( f'{name}_req{r}_hit_and_filled', 1, f'{name}_req{r}__hit_vld && ({name}_req{r}__hit_one_hot & {name}__filleds) == {name}_req{r}__hit_one_hot' )
        wirea( f'{name}_req{r}__needs_alloc', 1, f'{name}_req{r}_pvld && !{name}_req{r}__hit_vld' )
        if r != 0: hits += ' | '
        hits += f'{name}_req{r}__hit_one_hot'
        needs_allocs.append( f'{name}_req{r}__needs_alloc' )
    wirea( f'{name}__hits', tag_cnt, hits )
    wirea( f'{name}__needs_allocs', req_cnt, concata( needs_allocs, 1 ) )

    P()
    P(f'// {name} alloc' )
    P(f'//' )
    wirea( f'{name}__need_alloc_pvld', 1, f'|{name}__needs_allocs' )
    if custom_avails:
        wire( f'{name}__avails', tag_cnt )
    else:
        avails = []
        for i in range(tag_cnt):
            avails.append( f'{name}__need_alloc_pvld && !{name}__hits[{i}] && {name}__ref_cnt{i} == 0' )
        wirea( f'{name}__avails', tag_cnt, concata( avails, 1 ) )
    choose_eligible( f'{name}__alloc_avail_chosen_i', f'{name}__avails', tag_cnt, f'{name}__avail_preferred_i', gen_preferred=True )
    wirea( f'{name}__alloc_pvld', 1, f'{name}__avails_any_vld' )
    choose_eligible( f'{name}__alloc_req_chosen_i',  f'{name}__needs_allocs', req_cnt, f'{name}__alloc_req_preferred_i', gen_preferred=True )
    addrs = [ f'{name}_req{i}_addr' for i in range(req_cnt) ]
    muxa( f'{name}__alloc_addr', addr_w, f'{name}__alloc_req_chosen_i', addrs )
    binary_to_one_hot( f'{name}__alloc_avail_chosen_i', tag_cnt, r=f'{name}__alloc_avail_chosen_one_hot', pvld=f'{name}__alloc_pvld' )
    always_at_posedge()
    P(f'    if ( !{reset_} ) begin' )
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
            wirea( f'{name}_req{r}_status', 2, f'{name}_req{r}_hit_and_filled ? {name_uc}_HIT : {name}_req{r}__hit_vld ? {name_uc}_HIT_BEING_FILLED : {name_uc}_MISS' )
            dassert( f'!{name}_req{r}__needs_alloc || ({name}__alloc_pvld && {name}__alloc_req_chosen_i == {i})', f'{name} has can_always_alloc=True but can\'t alloc for req{r}' )
        else:
            wirea( f'{name}_req{r}_status', 2, f'{name}_req{r}_hit_and_filled ? {name_uc}_HIT : {name}_req{r}__hit_vld ? {name_uc}_HIT_BEING_FILLED : ({name}__alloc_pvld && {name}__alloc_req_chosen_i == {r}) ? {name_uc}_MISS : {name_uc}_MISS_CANT_ALLOC' )
        wirea( f'{name}_req{r}_tag_i', tag_i_w, f'{name}_req{r}__hit_vld ? {name}_req{r}__hit_i : {name}__alloc_avail_chosen_i' )
        sigs = { 'addr': addr_w, 
                 'tag_i': tag_i_w,
                 'status': 2 }
        if incr_ref_cnt_max > 1: sigs['incr_cnt'] = log2(incr_ref_cnt_max+1)
        iface_dprint( f'{name}_req{r}', sigs, f'{name}_req{r}_pvld' )

    P()
    P(f'// {name} decrements' )
    P(f'//' )
    decrs = ''
    for r in range(decr_req_cnt):
        binary_to_one_hot( f'{name}_decr{r}_tag_i', tag_cnt, f'{name}_decr{r}__one_hot', f'{name}_decr{r}_pvld' )
        if r != 0: decrs += ' | '
        decrs += f'{name}_decr{r}__one_hot'
        iface_dprint( f'{name}_decr{r}', { 'tag_i': tag_i_w }, f'{name}_decr{r}_pvld' )
    wirea( f'{name}__decrs', tag_cnt, decrs )

    P()
    P(f'// {name} fill' )
    P(f'//' )
    binary_to_one_hot( f'{name}_fill_tag_i', tag_cnt, f'{name}__fills', f'{name}_fill_pvld' )
    iface_dprint( f'{name}_fill', { 'tag_i': tag_i_w }, f'{name}_fill_pvld' )

    P()
    P(f'// {name} ref_cnt updates' )
    P(f'//' )
    always_at_posedge()
    P(f'    if ( !{reset_} ) begin' )
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

    P()
    P(f'// {name} filled updates' )
    P(f'//' )
    always_at_posedge()
    P(f'    if ( |{name}__alloc_avail_chosen_one_hot || {name}_fill_pvld ) begin' )
    P(f'        {name}__filleds <= (~{name}__alloc_avail_chosen_one_hot & {name}__filleds) | {name}__fills;' )
    P(f'    end' )
    P(f'end' )

    P()
    P(f'// {name} assertions' )
    P(f'//' )
    dassert_no_x( f'{name}__vlds' )
    dassert_no_x( f'{name}__filleds & {name}__vlds' )
    dassert_no_x( f'{name}__hits' )
    dassert_no_x( f'{name}__alloc_avail_chosen_one_hot' )
    dassert_no_x( f'{name}__fills' )
    dassert_no_x( f'{name}__decrs' )
    dassert( f'({name}__hits & {name}__alloc_avail_chosen_one_hot) === {tag_cnt}\'d0', f'{name} has hit and alloc to the same slot' )
    dassert( f'({name}__fills & {name}__filleds) === {tag_cnt}\'d0', 'f{name} has fill of already filled slot' )
    dassert( f'({name}__decrs & {name}__vlds) === {name}__decrs', f'{name} has decr-ref-cnt of slot with ref_cnt==0' )
    expr = ''
    for i in range(tag_cnt-1):
        for j in range(i+1, tag_cnt):
            if expr != '': expr += ' && '
            expr += f'(!{name}__vlds[{i}] || !{name}__vlds[{j}] || {name}__addr{i} !== {name}__addr{j})'
    dassert( f'{expr}', f'{name} has duplicate tags' )

    P()
    P(f'// {name} idle' )
    P(f'//' )
    idle = f'!{name}_fill_pvld'
    for i in range(tag_cnt): idle += f' && {name}__ref_cnt{i} == 0'
    for r in range(req_cnt): idle += f' && !{name}_req{r}_pvld' 
    wirea( f'{name}_idle', 1, idle )

def cache_filled_check( name, tag_i, r, tag_cnt, add_reg=True ):
    mux_subword( r, 1, tag_i, f'{name}__filleds', tag_cnt, add_reg=add_reg )
    
def module_footer( mn ):
    P()
    P(f'endmodule // {mn}' )
    global rams, fifos
    for ram  in rams:  make_ram( ram )
    for fifo in fifos: make_fifo( fifo )
    fifos = {}
    rams = {}

def tb_clk( decl_clk=True, default_cycles_max=2000, perf_op_first=100, perf_op_last=200 ):
    P()
    P(f'// {clk}' )
    P(f'//' )
    P(f'`ifndef VERILATOR' )
    if decl_clk: P(f'reg  {clk};' )
    P(f'real {clk}_phase; ' )
    P(f'real {clk}_period; ' )
    P(f'real {clk}_half_period; ' )
    P(f'' )
    P(f'initial begin ' )
    P(f'    if ( !$value$plusargs( "{clk}_phase=%f", {clk}_phase ) ) begin ' )
    P(f'        {clk}_phase = 0.0; ' )
    P(f'    end ' )
    P(f'    if ( !$value$plusargs( "{clk}_period=%f", {clk}_period ) ) begin ' )
    P(f'        {clk}_period = 1.0; ' )
    P(f'    end ' )
    P(f'    {clk}_half_period = {clk}_period / 2.0; ' )
    P(f'    {clk} = 0; ' )
    P(f'    #({clk}_half_period); ' )
    P(f'    #({clk}_phase); ' )
    P(f'    fork ' )
    P(f'        forever {clk} = #({clk}_half_period) ~{clk}; ' )
    P(f'    join ' )
    P(f'end ' )
    P(f'`endif' )
    P()
    P(f'reg [31:0] cycle_cnt;' )
    P(f'reg [31:0] cycles_max;' )
    P(f'initial begin' )
    P(f'    if ( !$value$plusargs( "cycles_max=%f", cycles_max ) ) begin ' )
    P(f'        cycles_max = {default_cycles_max};' )
    P(f'    end ' )
    P(f'    cycle_cnt = 0;' )
    P(f'end' )
    P()
    always_at_posedge()
    P(f'    if ( cycle_cnt === cycles_max ) begin' )
    P(f'        $display( "%0d: ERROR: cycles_max exceeded", $stime );' )
    P(f'        $fatal;' )
    P(f'    end else begin' )
    P(f'        cycle_cnt <= cycle_cnt + 1;' )
    P(f'        if ( cycle_cnt === {perf_op_first} ) $display( "(%0d) PERF BEGIN: I={perf_op_first}", $stime );' )
    P(f'        if ( cycle_cnt === {perf_op_last}  ) $display( "(%0d) PERF END: I={perf_op_last}", $stime );' )
    P(f'    end' )
    P(f'end' )

def tb_reset_( decl_reset_=True ):
    P()
    P(f'// {reset_} ' )
    P(f'// ' )
    if decl_reset_: P(f'reg {reset_};' )
    P(f'reg [31:0] {reset_}_cycle_cnt;' )
    P(f'initial begin ' )
    P(f'    {reset_} = 0; ' )
    P(f'    {reset_}_cycle_cnt = 0;' )
    P(f'end ' )
    P(f'always @( posedge {clk} ) begin' )
    P(f'    if ( !{reset_} ) begin' )
    P(f'        {reset_} <= {reset_}_cycle_cnt >= 10;' )
    P(f'        {reset_}_cycle_cnt <= {reset_}_cycle_cnt + 1;' )
    P(f'    end ' )
    P(f'end ' )

def tb_dump( module_name ):
    P()
    P(f'// DUMPs' )
    P(f'//' )
    P(f'initial begin' )
    P(f'`ifdef __NO_DUMP' )
    P(f'`else' )
    P(f'    if ( $test$plusargs( "dump" ) ) begin' )
    P(f'`ifdef __FSDB' )
    P(f'        $fsdbDumpfile( "{module_name}.fsdb" );' )
    P(f'        $fsdbDumpvars( 0, {module_name} );' )
    P(f'`else' )
    P(f'        $dumpfile( "{module_name}.lxt" );' )
    P(f'        $dumpvars( 0, {module_name} ); ' )
    P(f'`endif' )
    P(f'`endif' )
    P(f'    end' )
    P(f'end ' )
    P()
    P(f'// POWER SIM SAIF CAPTURE' )
    P(f'//' )
    P(f'`ifdef SAIF_TOP' )
    P(f'' )
    P(f'string saif_file;' )
    P(f'' )
    P(f'`define stringify( x ) `"x`"' )
    P(f'' )
    P(f'reg [63:0] saif_start_time;' )
    P(f'reg [63:0] saif_stop_time;' )
    P(f'' )
    P(f'initial begin' )
    P(f'`ifdef LIB_SAIF_VH' )
    P(f'    `include `stringify( LIB_SAIF_VH )' )
    P(f'`else' )
    P(f'    `include "lib_saif.vh"' )
    P(f'`endif' )
    P(f'    if ( !$value$plusargs( "saif_file=%s", saif_file ) ) begin' )
    P(f'        saif_file = `stringify( ``SAIF_TOP``.report.saif );' )
    P(f'    end' )
    P(f'    if ( !$value$plusargs( "saif_start_time=%d", saif_start_time ) ) begin' )
    P(f'        saif_start_time = 64\'h7fffffffffffffff;' )
    P(f'    end ' )
    P(f'    if ( !$value$plusargs( "saif_stop_time=%d", saif_stop_time ) ) begin' )
    P(f'        saif_stop_time = 0;' )
    P(f'    end ' )
    P()
    P(f'    $set_gate_level_monitoring( "on" );  ' )
    P(f'    $set_toggle_region( `stringify( `SAIF_TOP ) );     ' )
    P()
    P(f'    #(saif_start_time);' )
    P(f'    $display( "(%0d) Turning on SAIF toggle capture for %s", $stime, `stringify( `SAIF_TOP ) );' )
    P(f'    $toggle_start(); ' )
    P()
    P(f'    if ( saif_stop_time > saif_start_time ) begin' )
    P(f'        #(saif_stop_time-saif_start_time);' )
    P(f'        $display( "(%0d) Turning off SAIF toggle capture and writing %s", $stime, saif_file );' )
    P(f'        $toggle_stop; ' )
    P(f'        $toggle_report( saif_file, 1.0e-12, `stringify( `SAIF_TOP ) );  ' )
    P(f'    end' )
    P(f'end' )
    P()
    P(f'`endif' )


def tb_rand_init( default_rand_cycle_cnt=300 ):
    P()
    P(f'// {clk}_rand_cycle_cnt' )
    P(f'//' )
    P(f'reg [31:0] {clk}_rand_cycle_cnt;' )
    P(f'initial begin' )
    P(f'    if ( !$value$plusargs( "{clk}_rand_cycle_cnt=%f", {clk}_rand_cycle_cnt ) ) begin ' )
    P(f'        {clk}_rand_cycle_cnt = {default_rand_cycle_cnt}; ' )
    P(f'    end ' )
    P(f'end' )

def tb_randbits( sig, _bit_cnt ):
    global seed_z_init, seed_w_init, seed_i
    bit_cnt = _bit_cnt
    P()
    P(f'// {sig}' )
    P(f'//' )
    P(f'reg [{bit_cnt-1}:0] {sig};' )
    i = 0
    while bit_cnt != 0:
        sigi = sig if bit_cnt <= 32 else f'{sig}_{i}'
        this_bit_cnt = bit_cnt if bit_cnt <= 32 else 32
        bit_cnt -= this_bit_cnt
        lsb = i*32
        msb = lsb + this_bit_cnt - 1
        and_mask = '' if this_bit_cnt == 32 else f' & ((1 << {this_bit_cnt})-1)' 
        P(f'reg [31:0] {sigi}_m_z;' )
        P(f'reg [31:0] {sigi}_m_w;' )
        always_at_posedge()
        P(f'    if ( !{reset_} ) begin' )
        z_init = '32\'h%x' % seed_z_init
        w_init = '32\'h%x' % seed_w_init
        P(f'        {sigi}_m_z <= {z_init};' )
        P(f'        {sigi}_m_w <= {w_init};' )
        P(f'        {sig}[{msb}:{lsb}] <= (({w_init} << 16) + {w_init}){and_mask};' ) 
        P(f'    end else begin' )
        P(f'        {sigi}_m_z <= 36969 * {sigi}_m_z[15:0] + {sigi}_m_z[31:16];' )
        P(f'        {sigi}_m_w <= 18000 * {sigi}_m_w[15:0] + {sigi}_m_w[31:16];' )
        P(f'        {sig}[{msb}:{lsb}] <= (({sigi}_m_w << 16) + {sigi}_m_w){and_mask};' )
        P(f'    end' )
        P(f'end' )
        seed_z_init += 13
        seed_w_init += 57
        i += 1
    seed_i += 1

def tb_randomize_sigs( sigs, pvld, prdy='', cycle_cnt='', prefix='' ):
    P()
    P(f'// randomize signals' )
    P(f'// For now, we let 50% of bits change each cycle (worst-case).' )
    P(f'//' )
    if cycle_cnt == '': cycle_cnt = f'{clk}_rand_cycle_cnt'
    if prefix    == '': prefix = f'rand{seed_i}'
    if prdy      != '': prdy = f'({prdy}) && '
    bit_cnt = 0;
    reg( pvld, 1 )
    for sig in sigs: 
        w = sigs[sig][0] if isinstance( sigs[sig], list ) else sigs[sig]
        bit_cnt += w
        reg( sig, w )
    
    tb_randbits( f'{prefix}_bits', bit_cnt )

    P(f'reg [31:0] {prefix}_cnt;' )
    always_at_posedge()
    P(f'    if ( !{reset_} ) begin' )
    P(f'        {pvld} <= 0;' )
    P(f'        {prefix}_cnt <= 0;' )
    P(f'    end else if ( {prdy}{prefix}_cnt <= {cycle_cnt} ) begin' )
    P(f'        {pvld} <= {prefix}_cnt != 0;' )
    lsb = 0
    for sig in sigs:
        if isinstance( sigs[sig], list ):
            w   = sigs[sig][0]
            min = sigs[sig][1]
            max = sigs[sig][2]
            msb  = lsb + w - 1
            P(f'        {sig} <= {min} + ({prefix}_bits[{msb}:{lsb}] % ({max} - {min} + 1));' )
        else:
            msb  = lsb + sigs[sig] - 1
            P(f'        {sig} <= {prefix}_bits[{msb}:{lsb}];' )
        lsb  = msb + 1
    P(f'        {prefix}_cnt = {prefix}_cnt + 1;' )
    P(f'    end else begin' )
    P(f'        {pvld} <= 0;' )
    P(f'    end' )
    P(f'end' )
    P()
    dprint( prefix, sigs, pvld )

def tb_ram_decl( ram_name, d, sigs ):
    w = iface_width( sigs )
    P(f'reg [{w-1}:0] {ram_name}[0:{d-1}];' )

def tb_ram_file( ram_name, file_name, sigs, is_hex_data=True ):
    d = S.file_line_cnt( file_name )
    if d == 0: S.die( f'{file_name} is empty' )
    tb_ram_decl( ram_name, d, sigs )
    hb = 'h' if is_hex_data else 'b'
    P(f'initial $readmem{hb}( "{file_name}", {ram_name} );' )

def tb_ram_read( ram_name, row, oname, sigs, do_decl=True ):
    iface_split( f'{ram_name}[{row}]', oname, sigs, do_decl )

def tb_ram_write( ram_name, row, iname, sigs, do_decl=True ):
    iface_combine( iname, f'{ram_name}[{row}]', sigs, do_decl )

#-----------------------------------------------------------------
# Partial testbench for logic in this file.
#-----------------------------------------------------------------
def make_v( module_name ):
    pass

def make_tb( name, module_name ):
    module_header_begin( f'tb_{module_name}' )
    module_header_end()
    P()
    tb_clk( default_cycles_max=10000 )
    tb_reset_()
    tb_dump( f'tb_{module_name}' )
    P()
    tb_rand_init()

    P()
    P(f'//----------------------------------------' )
    P(f'// one pulse to combinational logic below' )
    P(f'//----------------------------------------' )
    reg( f'combo_pvld_p', 1 )
    reg( f'combo_pvld', 1 )
    always_at_posedge()
    P(f'    if ( !{reset_} ) begin' )
    P(f'        combo_pvld_p <= 1;' )
    P(f'        combo_pvld <= 0;' )
    P(f'    end else begin' )
    P(f'        combo_pvld <= combo_pvld_p;' )
    P(f'        combo_pvld_p <= 0;' )
    P(f'    end' )
    P(f'end' )

    P()
    P(f'//----------------------------------------' )
    P(f'// concata(), unconcata()' )
    P(f'// collapse(), uncollapse()' )
    P(f'//----------------------------------------' )
    wirea( 'mask',   4, '4\'b1010' )
    wirea( 'addr0', 32, '32\'h10000' )
    wirea( 'addr1', 32, '32\'h20000' )
    wirea( 'addr2', 32, '32\'h40000' )
    wirea( 'addr3', 32, '32\'h50000' )
    addrs = [ f'addr{i}' for i in range(4) ]
    concata( addrs, 32, f'addrs' )
    collapse( 'mask', 4, f'collapsed', { 'addrs': [ 32, 'addrs' ] } )
    unconcata( 'collapsed_addrs', 4, 32, f'collapsed_addr' )
    unconcata( 'collapsed_indexes', 4, 2, f'collapsed_index' )
    P()
    uncollapse( 'collapsed_vlds', 'collapsed_indexes', 4, { 'addrs': [ 32, 'collapsed_addrs' ],
                                                            'indexes': [ 2, 'collapsed_indexes' ] }, 'uncollapsed' )
    unconcata( 'uncollapsed_addrs', 4, 32, f'uncollapsed_addr' )
    unconcata( 'uncollapsed_indexes', 4, 2, f'uncollapsed_index' )

    P()
    P(f'//----------------------------------------' )
    P(f'// concata(), unconcata()' )
    P(f'// collapse(), uncollapse()' )
    P(f'// But with 1-bit mask' )
    P(f'//----------------------------------------' )
    wirea( 'mask1', 1, '1\'b1' )
    addrs = [ f'addr{i}' for i in range(1) ]
    concata( addrs, 32, f'addrs1' )
    collapse( 'mask1', 1, f'collapsed1', { 'addrs': [ 32, 'addrs1' ] } )
    unconcata( 'collapsed1_addrs', 1, 32, f'collapsed1_addr' )
    unconcata( 'collapsed1_indexes', 1, 1, f'collapsed1_index' )
    P()
    uncollapse( 'collapsed1_vlds', 'collapsed1_indexes', 1, { 'addrs': [ 32, 'collapsed1_addrs' ],
                                                              'indexes': [ 1, 'collapsed1_indexes' ] }, 'uncollapsed1' )
    unconcata( 'uncollapsed1_addrs', 1, 32, f'uncollapsed1_addr' )
    unconcata( 'uncollapsed1_indexes', 1, 1, f'uncollapsed1_index' )
    
    P()
    P(f'//----------------------------------------' )
    P(f'// choose_eligibles()' )
    P(f'//----------------------------------------' )
    wirea( 'avails', 8, '8\'b10000010' )
    wirea( 'reqs', 4, '4\'b1101' )
    choose_eligibles( 'arb', 'avails', 8, 'avail_preferred_i', 'reqs', 4, gen_preferred=True )
    unconcata( 'arb_elig_req_indexes', 8, 2, 'arb_elig_req_index' )
    for i in range(8): muxa( f'alloc_addr{i}', 32, f'arb_elig_req_index{i}', addrs )

    P()
    P(f'endmodule // tb_{module_name}' )
