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

def reinit( _clk='clk', _reset_='reset_', _vdebug=True, _vassert=True ):
    global clk, reset_, vdebug, vassert
    global module_name, fifos
    global seed_z_init, seed_w_init, seed_i
    global io
    global in_module_header
    clk = _clk
    reset_ = _reset_
    vdebug = _vdebug
    vassert = _vassert
    module_name = ''
    io = []
    in_module_header = False
    fifos  = {}
    seed_z_init = 0x12345678
    seed_w_init = 0xbabecaf3
    seed_i = 0

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
    global fifos
    global io
    global in_module_header
    if in_module_header: S.die( 'module_header_begin() called while already in a module header' )
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
def sreg( name, w ):       decl( 'reg signed', name, w )

#-------------------------------------------
# Common Verilog code wrappers
#-------------------------------------------
def always_at_posedge( _clk='' ):
    if _clk == '': _clk = clk
    P( f'always @( posedge {_clk} ) begin' )

#-------------------------------------------
# Replicate expression cnt times as a concatenation
#-------------------------------------------
def repl( expr, cnt ):
    return f'{{{cnt}{{{expr}}}}}'

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
# Concatenate expressions stored in an array.
# Optionally generate a wire assignment.
# Optionally concatenate in reverse order, which is common for eligible masks.
#-------------------------------------------
def concata( vals, r='', reverse=False ):
    expr = ''
    for v in vals:
        if reverse:
            if expr != '': expr = ', ' + expr
            expr = v + expr
        else:
            if expr != '': expr += ', '
            expr += v
    expr = f'{{{expr}}}'
    if r != '': wirea( r, len(vals), expr )
    return expr

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

def iface_concat( iname, sigs ):
    if len(sigs) == 0: S.die( 'iface_concat: empty sigs list' )
    concat = ''
    for sig in sigs:
        if concat != '': concat += ','
        if iname != '': concat += f'{iname}_'
        concat += sig
    if len(sigs) == 1:
        return concat
    else:
        return f'{{{concat}}}'

def iface_combine( iname, oname, sigs, do_decl=True ):
    if do_decl: wire( oname, iface_width(sigs) )
    iconcat = iface_concat( iname, sigs )
    assign = 'assign ' if do_decl else '    '
    P(f'{assign}{oname} = {iconcat};' )

def iface_split( iname, oname, sigs, do_decl=True ):
    if do_decl: iface_wire( oname, sigs )
    oconcat = iface_concat( oname, sigs )
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

def iface_stageN( p, sigs, pvld, prdy='' ):
    iface_stage( f'p{p}', f'p{p+1}', sigs, pvld, prdy )

def iface_dprint( name, sigs, pvld, prdy='', use_hex_w=16, with_clk=True, indent='' ):
    isigs = {}
    for sig in sigs: isigs[f'{name}_{sig}'] = sigs[sig]
    vld = pvld
    if prdy != '': vld += f' && {prdy}'
    dprint( name, isigs, vld, use_hex_w=16, with_clk=with_clk, indent=indent )

def module_header_end():
    global in_module_header
    global io
    if not in_module_header: S.die( 'module_header_end() called while not already in a module header' )
    ports_s = ''
    io_s = ''
    for i in range( len(io) ):
        if io[i]['name'] != '':
            if i != 0: ports_s = ', ' + ports_s
            ports_s = io[i]['name'] + ports_s

    if ports_s != '': ports_s = f'( {ports_s} )'

    P()
    P(f'module {module_name}{ports_s};' )
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
    w = log2( len(names) )
    for i in range(len(names)):
        wirea( f'{prefix}{names[i]}', w, i )

def display( msg, sigs, use_hex_w=16, prefix='        ' ):
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
    fmt = f'%0d: {msg}: {fmt}     in %m'
    P( f'{prefix}$display( "{fmt}", $stime{vals} );' )

def dprint( msg, sigs, pvld, use_hex_w=16, with_clk=True, indent='' ):
    if not vdebug: return
    P(f'// synopsys translate_off' )
    prefix = indent
    if with_clk: prefix += f'always @( posedge {clk} ) '
    if pvld != '': prefix += f'if ( {pvld} ) '
    display( msg, sigs, use_hex_w, prefix )
    P(f'// synopsys translate_on' )

def dassert( expr, msg, pvld='', with_clk=True, indent='    ' ):
    if not vassert: return
    P(f'// synopsys translate_off' )
    if with_clk: always_at_posedge()
    reset_test = f'{reset_} === 1\'b1 && ' if with_clk else ''
    pvld_test  = f'({pvld}) && '             if pvld != '' else ''
    P(f'{indent}if ( {reset_test}{pvld_test}(({expr}) !== 1\'b1) ) begin' )
    P(f'{indent}    $display( "%0d: ERROR: {msg}", $stime );' )
    P(f'{indent}    $fatal;' )
    P(f'{indent}end' )
    if with_clk: P(f'end' )
    P(f'// synopsys translate_on' )
   
def dassert_no_x( expr, pvld='', with_clk=True, indent='    ' ):
    dassert( f'^({expr}) !== 1\'bx', f'found an X in: {expr}', pvld, with_clk, indent )

#-------------------------------------------
# For MUX, values need not be constants
#-------------------------------------------
def muxa( r, w, sel, vals, add_reg=True ):
    sw = log2( len(vals) )
    if add_reg:
        P(f'reg [{w-1}:0] {r};' )
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
# rotate bits left or right by N (useful for round-robin scheduling)
#-------------------------------------------
def rotate_left( r, w, n, bits ):
    vals = []
    for i in range( w ):
        vals.append( bits if i == 0 else f'{{{bits}[{w-i-1}:0], {bits}[{w-1}:{w-i}]}}' )
    return muxa( r, w, n, vals )

def rotate_right( r, w, n, bits ):
    vals = []
    for i in range( w ):
        vals.append( bits if i == 0 else f'{{{bits}[{w-1}:{w-i}], {bits}[{w-i-1}:0]}}' )
    return muxa( r, w, n, vals )

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
        P(f'wire [{w-1}:0] {r} = ({r}_add >= {c}) ? ({r}_add - {c}) : {r}_add;' )
    return r

def wrapped_sub( r, w, a, b, c ):
    if is_pow2( c ):
        P(f'wire [{w-1}:0] {r} = {a} - {b};' )
    else:
        P(f'wire [{w}:0] {r}_sub = {a} - {b};' )
        P(f'wire [{w-1}:0] {r} = ({r}_sub >= {c}) ? ({r}_sub + {c}) : {r}_sub;' )
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
    if ~custom_cla: 
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
        P(f'wire {r}_s{s}_P{j} = {a}[{j}] | {b}[{j}];' )
        P(f'wire {r}_s{s}_G{j} = {a}[{j}] & {b}[{j}];' )
        h[j] = 0

    # stage 1,2,... P/G bits
    ww = w
    s = 1
    while ww > 1:
        j0 = 0
        while j0 < (w-1):
            j1       = j0 + 1
            s0       = h[j0]
            s1       = h[j1]
            P(f'wire {r}_s{s}_P{j1} = {r}_s{s0}_P{j0} & {r}_s{s0}_P{j1};' )
            P(f'wire {r}_s{s}_G{j1} = {r}_s{s0}_G{j1} | ({r}_s{s0}_G{j0} & {r}_s{s0}_P{j0});' )
            h[j1]    = s
            j0      += 1 << s
        ww = (ww+1) >> 1
        s += 1

    # carry out bits
    P(f'wire ' + r + '_C0 = ' + str(cin) + ';' )
    for j0 in range(w-1):
        s0 = h[j0]
        P(f'wire {r}_C{j0+1} = {r}_s{s0}_G{j0} | ({r}_C{j0} & {r}_s{s0}_P{j0});' )

    # sum bits
    wire( f'{r}_S', N=2 )
    for j in range(w):
        P(f'assign {r}_S[{j}] = {r}_C{j} ^ {r}_s{h[j]}_G{j};' )
    return f'{r}_S'

#-------------------------------------------
# count zeroes/ones
#-------------------------------------------
def count_zeroes( x, x_w, r='' ):
    sum = ""
    for i in range( x_w ):
        if i != 0: sum += ' + '
        sum += f'!{x}[{i}]'
    if r != '': wirea( r, log2(x_w+1), sum )
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
    if add_reg: reg( f'{x}{suff}', cnt_w )
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
    if add_reg: reg( f'{x}{suff}', cnt_w )
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
# determine if a one_hot mask is really a one-hot mask
# there should be at most one bit set
#-------------------------------------------
def is_one_hot( mask, mask_w, r='' ):
    ioh = count_ones( mask, mask_w ) + ' <= 1'
    if r != '': V.wirea( r, 1, ioh )
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
# compute integer log2( x ) in hardware
#-------------------------------------------
def vlog2( x, x_w ):
    cnt_w = value_bitwidth( x_w )
    ldz = count_leading_zeroes( x, x_w )
    P(f'wire [{cnt_w-1}:0] {x}_lg2 = {cnt_w}\'d{x_w-1} - {ldz};' )
    
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
# choose eligible from mask and preferred 
#
# note: elig_mask should be left-to-right order, not right-to-left
#-------------------------------------------
def choose_eligible( r, elig_mask, cnt, preferred, gen_preferred=False, adv_preferred='' ):
    w = log2( cnt )
    if gen_preferred: 
        reg( preferred, w )
    reverse( elig_mask, cnt, f'{elig_mask}_r' )
    prio_elig_mask = rotate_left( f'{r}_prio_elig_mask', cnt, preferred, f'{elig_mask}_r' )
    choice = count_leading_zeroes( prio_elig_mask, cnt )
    if is_pow2( cnt ):
        wirea( r, w, f'{preferred} + {choice}' )
    else:
        wirea( f'{r}_p', w+1, f'{preferred} + {choice}' )
        wirea( r, w, f'({r}_p >= {cnt} ? ({r}_p - {cnt}) : {r}_p' )
    if gen_preferred:
        P(f'wire {elig_mask}_any_vld = |{elig_mask};' )
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
    while cnt > 1: 
        new_vlds    = []
        new_prios   = []
        new_choices = []
        for j in range((cnt+1) >> 1):
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
    wirea(f'{r}_vld', 1, vlds[0] )
    cnt = len(vlds)
    wirea(f'{r}_i', choice_w, choices[0] )

#-------------------------------------------
# resource accounting for <cnt> resource slots
#-------------------------------------------
def resource_accounting( name, cnt, add_free_cnt=False, set_i_is_free_i=False ):
    P()
    reg( f'{name}_in_use', cnt )
    reverse( f'{name}_in_use', cnt, f'{name}_in_use_r' )
    count_leading_ones( f'{name}_in_use_r', cnt )
    wirea( f'{name}_free_pvld', 1, f'!(&{name}_in_use)' )
    wirea( f'{name}_free_i', log2(cnt), f'{name}_in_use_r_ldo' )
    if add_free_cnt: count_zeroes( f'{name}_in_use', cnt, f'{name}_free_cnt' )
    wire( f'{name}_set_pvld', 1 )
    if set_i_is_free_i:
        wirea( f'{name}_set_i', log2(cnt), f'{name}_free_i' )
    else:
        wire( f'{name}_set_i', log2(cnt) )
    wire( f'{name}_clr_pvld', 1 )
    wire( f'{name}_clr_i', log2(cnt) )
    always_at_posedge()
    P(f'    if ( !{reset_} ) begin' )
    P(f'        {name}_in_use <= 0;' )
    P(f'    end else if ( {name}_set_pvld || {name}_clr_pvld ) begin' )
    P(f'        {name}_in_use <= ({name}_in_use & ~({name}_clr_pvld << {name}_clr_i)) | ({name}_set_pvld << {name}_set_i);' )
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

def fifo( sigs, pvld, prdy, depth, with_wr_prdy=True, prefix='d_', u_name='' ):
    if depth > 1: depth += 1
    P()
    names = ', '.join( sigs.keys() )
    P(f'// {depth}-deep fifo for: {names}' )
    P(f'//' )
    w = 0

    ins = ''
    outs = ''
    d_pvld = f'{prefix}{pvld}'
    d_prdy = f'{prefix}{prdy}'
    if with_wr_prdy: 
        wire( prdy, 1 )
    else:
        prdy = ''
    wire( d_pvld, 1 )
    wire( d_prdy, 1 )
    for sig in sigs:
        w += sigs[sig]
        wire( f'{prefix}{sig}', sigs[sig] )
        if ins  != '': ins  += ', '
        if outs != '': outs += ', '
        ins += sig
        outs += f'{prefix}{sig}'
    
    name = f'{module_name}_fifo_{depth}x{w}'
    if u_name == '': u_name = f'u_{name}'
    fifos[name] = {'depth': depth, 'w': w}

    P(f'{name} {u_name}( .{clk}({clk}), .{reset_}({reset_}),' )
    P(f'                        .wr_pvld({pvld}), .wr_prdy({prdy}), .wr_pd('+'{'+f'{ins}'+'}),' )
    P(f'                        .rd_pvld({d_pvld}), .rd_prdy({d_prdy}), .rd_pd('+'{'+f'{outs}'+'}) );' )
    if with_wr_prdy:
        P(f'// synopsys translate_off' )
        always_at_posedge()
        P(f'    if ( {reset_} === 1 && {pvld} !== 0 && {prdy} !== 1 ) begin' )
        P(f'        $display( "%0d: %m: ERROR: fifo wr_pvld=%d but wr_prdy=%d", $stime, {pvld}, {prdy} );' )
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

def cache_tags( name, addr_w, tag_cnt, req_cnt, ref_cnt_max, incr_ref_cnt_max=1, decr_req_cnt=0, can_always_alloc=False ):
    if incr_ref_cnt_max < 1: S.die( f'cache_tags: incr_ref_cnt_max needs to be at least 1' )
    if decr_req_cnt == 0: decr_req_cnt = req_cnt

    P()
    P(f'// {name} cache tags: addr_w={addr_w} tag_cnt={tag_cnt} req_cnt={req_cnt} ref_cnt_max={ref_cnt_max}' )
    P(f'//' )
    tag_i_w = log2( tag_cnt )
    name_uc = name.upper()
    enum( f'{name_uc}_', ['MISS_CANT_ALLOC', 'MISS', 'HIT', 'HIT_BEING_FILLED'] )
    ref_cnt_w = log2( ref_cnt_max+1 )
    for i in range(tag_cnt): reg( f'{name}__ref_cnt{i}', ref_cnt_w )
    wirea( f'{name}__vlds', tag_cnt, concata( [f'|{name}__ref_cnt{i}' for i in range(tag_cnt)], reverse=True ) )
    for i in range(tag_cnt): reg( f'{name}__addr{i}', addr_w )
    reg( f'{name}__filleds', tag_cnt )

    wirea( f'{name}__avails', tag_cnt, concata( [f'{name}__ref_cnt{i} == 0' for i in range(tag_cnt)], reverse=True ) )
    wire( f'{name}__alloc_vld', 1 )
    choose_eligible( f'{name}__avail_i', f'{name}__avails', tag_cnt, f'{name}__avail_preferred_i', gen_preferred=True, adv_preferred=f'{name}__alloc_vld' )
    wirea( f'{name}__avail_vld', 1, f'|{name}__avails_any_vld' )

    avail_vld = f'{name}__avail_vld'
    alloc_vld = ''
    hits = ''
    for r in range(req_cnt):
        P()
        P(f'// {name}_req{r}' )
        P(f'//' )
        P(f'// TODO: hit_one_hot needs to take into account a slot allocated by a prior requestor for the same line' )
        P(f'//' )
        wirea( f'{name}_req{r}__hit_one_hot', tag_cnt, concata( [f'{name}_req{r}_pvld && {name}__vlds[{i}] && {name}_req{r}_addr == {name}__addr{i}' for i in range(tag_cnt)], reverse=True ) )
        one_hot_to_binary( f'{name}_req{r}__hit_one_hot', tag_cnt, f'{name}_req{r}__hit_i', f'{name}_req{r}__hit_vld' )
        wirea( f'{name}_req{r}_hit_and_filled', 1, f'{name}_req{r}__hit_vld && ({name}_req{r}__hit_one_hot & {name}__filleds) == {name}_req{r}__hit_one_hot' )
        wirea( f'{name}_req{r}__needs_alloc', 1, f'{name}_req{r}_pvld && !{name}_req{r}__hit_vld' )
        if can_always_alloc:
            wirea( f'{name}_req{r}_status', 2, f'{name}_req{r}_hit_and_filled ? {name_uc}_HIT : {name}_req{r}__hit_vld ? {name_uc}_HIT_BEING_FILLED : {name_uc}_MISS' )
            dassert( f'{name}_req{r}__needs_alloc === 1\'b0 || ({avail_vld}) === 1\'b1', f'{name} has can_always_alloc=True but can\'t alloc for req{r}' )
        else:
            wirea( f'{name}_req{r}_status', 2, f'{name}_req{r}_hit_and_filled ? {name_uc}_HIT : {name}_req{r}__hit_vld ? {name_uc}_HIT_BEING_FILLED : ({avail_vld}) ? {name_uc}_MISS : {name_uc}_MISS_CANT_ALLOC' )
        wirea( f'{name}_req{r}_tag_i', tag_i_w, f'{name}_req{r}__hit_vld ? {name}_req{r}__hit_i : {name}__avail_i' )
        if r != 0: alloc_vld += ' || '
        alloc_vld += f'{name}_req{r}__needs_alloc'
        if r != 0: avail_vld += ' && '
        avail_vld += f'!{name}_req{r}__needs_alloc'
        if r != 0: hits += ' | '
        hits += f'{name}_req{r}__hit_one_hot'
        sigs = { 'addr': addr_w, 
                 'tag_i': tag_i_w,
                 'status': 2 }
        if incr_ref_cnt_max > 1: sigs['incr_cnt'] = log2(incr_ref_cnt_max+1)
        iface_dprint( f'{name}_req{r}', sigs, f'{name}_req{r}_pvld' )
    wirea( f'{name}__hits', tag_cnt, hits )

    P()
    P(f'// {name}_alloc' )
    P(f'//' )
    P(f'assign {name}__alloc_vld = {alloc_vld};' )
    binary_to_one_hot( f'{name}__avail_i', tag_cnt, f'{name}__allocs', f'{name}__alloc_vld' )
    always_at_posedge()
    for i in range(tag_cnt):
        addr_expr = f'{name}_req0_addr'  # TODO: needs to change if multiple requestors
        P(f'    if ( {name}__alloc_vld && {name}__avail_i == {i} ) {name}__addr{i} <= {addr_expr};' )
    P(f'end' )

    decrs = ''
    for r in range(decr_req_cnt):
        P()
        P(f'// {name}_decr{r}' )
        P(f'//' )
        binary_to_one_hot( f'{name}_decr{r}_tag_i', tag_cnt, f'{name}_decr{r}__one_hot', f'{name}_decr{r}_pvld' )
        if r != 0: decrs += ' | '
        decrs += f'{name}_decr{r}__one_hot'
        iface_dprint( f'{name}_decr{r}', { 'tag_i': tag_i_w }, f'{name}_decr{r}_pvld' )
    wirea( f'{name}__decrs', tag_cnt, decrs )

    P()
    P(f'// {name}_fill' )
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
        bool_expr = f'{name}__allocs[{i}]'
        sum_expr = f'{name}__ref_cnt{i}'
        if incr_ref_cnt_max == 1: 
            sum_expr += f' + {name}__allocs[{i}]'
        for r in range(req_cnt):
            if incr_ref_cnt_max > 1:
                dassert( f'!{name}_req{r}_pvld || {name}_req{r}_incr_cnt != 0', f'{name}_req{r}_incr_cnt must be at least 1', with_clk=False, indent='        ' )
            bool_expr += f' || {name}_req{r}__hit_one_hot[{i}]'
            if incr_ref_cnt_max == 1:
                sum_expr  += f' + {name}_req{r}__hit_one_hot[{i}]'
            else:
                sum_expr  += f' + (({name}__allocs[{i}] || {name}_req{r}__hit_one_hot[{i}]) ? {name}_req{r}_incr_cnt : 0)'
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
    P(f'    if ( {name}__alloc_vld || {name}_fill_pvld ) begin' )
    P(f'        {name}__filleds <= (~{name}__allocs & {name}__filleds) | {name}__fills;' )
    P(f'    end' )
    P(f'end' )

    P()
    P(f'// {name} assertions' )
    P(f'//' )
    dassert_no_x( f'{name}__vlds' )
    dassert_no_x( f'{name}__filleds & {name}__vlds' )
    dassert_no_x( f'{name}__hits' )
    dassert_no_x( f'{name}__allocs' )
    dassert_no_x( f'{name}__fills' )
    dassert_no_x( f'{name}__decrs' )
    dassert( f'({name}__hits & {name}__allocs) === {tag_cnt}\'d0', f'{name} has hit and alloc to the same slot' )
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
    global fifos
    for fifo in fifos:
        make_fifo( fifo )
    fifos = {}

def tb_clk( decl_clk=True, default_cycles_max=2000, perf_op_first=100, perf_op_last=200 ):
    P(f'' )
    P(f'// {clk}' )
    P(f'//' )
    if decl_clk: P(f'reg  {clk};' )
    P(f'real {clk}_phase; ' )
    P(f'real {clk}_period; ' )
    P(f'real {clk}_half_period; ' )
    P(f'reg [31:0] cycle_cnt;' )
    P(f'reg [31:0] cycles_max;' )
    P(f'' )
    P(f'initial begin ' )
    P(f'    if ( !$value$plusargs( "{clk}_phase=%f", {clk}_phase ) ) begin ' )
    P(f'        {clk}_phase = 0.0; ' )
    P(f'    end ' )
    P(f'    if ( !$value$plusargs( "{clk}_period=%f", {clk}_period ) ) begin ' )
    P(f'        {clk}_period = 1.0; ' )
    P(f'    end ' )
    P(f'    if ( !$value$plusargs( "cycles_max=%f", cycles_max ) ) begin ' )
    P(f'        cycles_max = {default_cycles_max};' )
    P(f'    end ' )
    P(f'    {clk}_half_period = {clk}_period / 2.0; ' )
    P(f'    {clk} = 0; ' )
    P(f'    cycle_cnt = 0;' )
    P(f'    #({clk}_half_period); ' )
    P(f'    #({clk}_phase); ' )
    P(f'    fork ' )
    P(f'        forever {clk} = #({clk}_half_period) ~{clk}; ' )
    P(f'    join ' )
    P(f'end ' )
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
    P(f'' )
    P(f'// {reset_} ' )
    P(f'// ' )
    if decl_reset_: P(f'reg {reset_};' )
    P(f'initial begin ' )
    P(f'    {reset_} = 0; ' )
    P(f'    repeat( 10 ) @( posedge {clk} ); ' )
    P(f'    {reset_} <= 1; ' )
    P(f'end ' )

def tb_dump( module_name ):
    P(f'// DUMPs' )
    P(f'//' )
    P(f'initial begin' )
    P(f'`ifdef __NO_DUMP' )
    P(f'`else' )
    P(f'`ifdef __FSDB' )
    P(f'    $fsdbDumpfile( "{module_name}.fsdb" );' )
    P(f'    $fsdbDumpvars( 0, {module_name} );' )
    P(f'`else' )
    P(f'    $dumpfile( "{module_name}.lxt" );' )
    P(f'    $dumpvars( 0, {module_name} ); ' )
    P(f'`endif' )
    P(f'`endif' )
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
