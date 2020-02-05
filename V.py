# V.py - utility functions for generating Verilog
#
import S
import config as C

P = print

def reinit():
    global module_name, fifos
    global seed_z_init, seed_w_init
    global io
    global in_module_header
    module_name = ''
    io = []
    in_module_header = False
    fifos  = {}
    seed_z_init = 0x12345678;
    seed_w_init = 0xbabecaf3;

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
    global io
    if is_io:
        io.append( { 'name': name, 'kind': kind, 'width': w } )
    else:
        P( kind + ' ' + (('[' + str(w-1) + ':' + '0] ') if w != 1 else '') + name + ';' )

def decla( kind, name, w, v ):
    P( kind + ' ' + (('[' + str(w-1) + ':' + '0] ') if w != 1 else '') + name + ' = ' + f'{v}' + ';' )

def input( name, w ):      
    decl( 'input ', name, w, True )

def sinput( name, w ):     
    decl( 'input signed ', name, w, True )

def output( name, w ):     
    decl( 'output', name, w, True )

def soutput( name, w ):    
    decl( 'output signed', name, w, True )

def module_header_end():
    global in_module_header
    global io
    if not in_module_header: S.die( 'module_header_end() called while not already in a module header' )
    ports_s = ''
    io_s = ''
    for i in range( len(io) ):
        if i != 0: ports_s = ', ' + ports_s
        ports_s = io[i]['name'] + ports_s

    if ports_s != '': ports_s = f'( {ports_s} )'

    P()
    P(f'module {module_name}{ports_s};' )
    P()
    for i in range( len(io) ):
        w = io[i]['width']
        P( io[i]['kind'] + ' ' + (('[' + str(w-1) + ':' + '0] ') if w != 1 else '') + io[i]['name'] + ';' )
    P()
    in_module_header = False
    io = []

def wire( name, w ):       decl( 'wire', name, w )
def wirea( name, w, v ):   decla( 'wire', name, w, v )
def swire( name, w ):      decl( 'wire signed', name, w )
def swirea( name, w, v ):  decla( 'wire signed', name, w, v )
def reg( name, w ):        decl( 'reg', name, w )
def sreg( name, w ):       decl( 'reg signed', name, w )

def enum( prefix, names ):
    w = C.log2( len(names) )
    for i in range(len(names)):
        wirea( f'{prefix}{names[i]}', w, i )

def dprint( msg, sigs, pvld, use_hex_w=16 ):
    if not C.vdebug: return
    fmt = ''
    vals = ''
    for sig in sigs:
        w = sigs[sig]
        if w == 0:
            fmt += sig   # just text
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
    P(f'// synopsys translate_off' )
    P(f'always @( posedge {C.clk} ) if ( {pvld} ) $display( "{fmt}", $stime{vals} );' )
    P(f'// synopsys translate_on' )

def dassert( expr, msg, pvld ):
    if not C.vassert: return
    P(f'// synopsys translate_off' )
    P(f'always @( posedge {C.clk} ) begin' )
    P(f'    if ( {C.reset_} === 1\'b1 && ({pvld}) && (({expr}) !== 1\'b1) ) begin' )
    P(f'        $display( "%0d: ERROR: {msg}", $stime );' )
    P(f'        $fatal;' )
    P(f'    end' )
    P(f'end' )
    P(f'// synopsys translate_on' )
    
#-------------------------------------------
# reverse bits (wires only)
#-------------------------------------------
def reverse( bits, w, rbits='' ):
    if rbits == '': rbits = f'{bits}_r' 
    P(f'reg [{w-1}:0] {rbits};' )
    i = f'{rbits}_i'
    P(f'integer {i}; always @(*) for( {i} = 0; {i} < {w}; {i} = {i} + 1 ) {rbits}[{i}] = {bits}[{w-1}-{i}]; // reverses bits; generates no logic' )
    return rbits

#-------------------------------------------
# For MUX, values need not be constants
#-------------------------------------------
def muxa( r, w, sel, vals ):
    sw = C.log2( len(vals) )
    P(f'reg [{w-1}:0] {r};' )
    P(f'always @( * ) begin' )
    P(f'    case( {sel} )' )
    for i in range(len(vals)):
        P(f'        {sw}\'d{i}: {r} = {vals[i]};' )
    P(f'        default: {r} = {w}\'d0;' )
    P(f'    endcase' )
    P(f'end' )
    return r

def mux( r, w, sel, *vals ): 
    return muxa( r, w, sel, vals )

#-------------------------------------------
# MUX_SUBWORD, mux subwords
#-------------------------------------------
def mux_subword( r, w, sel, word, word_w ):
    sw_cnt = int( (word_w + w - 1) / w )
    lsb = 0
    vals = []
    for i in range(sw_cnt):
        msb = lsb + w - 1
        if msb >= word_w: msb = word_w - 1
        vals.append( f'{word}[{msb}:{lsb}]' )
        lsb = msb + 1
    return mux( r, w, sel, *vals )

#-------------------------------------------
# MUXN, multiple signals and sets of values are supported
#-------------------------------------------
def muxN( sigs, sel, vals ):
    sw = C.log2( len(vals) )
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
# We assume that A and B are unsigned and already < C.
# C is a constant.
#---------------------------------------------------------
def wrapped_add( r, w, a, b, c ):
    if C.is_pow2( c ):
        P(f'wire [{w-1}:0] {r} = {a} + {b};' )
    else:
        P(f'wire [{w}:0] {r}_add = {a} + {b};' )
        P(f'wire [{w-1}:0] {r} = ({r}_add >= {c}) ? ({r}_add - {c}) : {r}_add;' )
    return r

def wrapped_sub( r, w, a, b, c ):
    if C.is_pow2( c ):
        P(f'wire [{w-1}:0] {r} = {a} - {b};' )
    else:
        P(f'wire [{w}:0] {r}_sub = {a} - {b};' )
        P(f'wire [{w-1}:0] {r} = ({r}_sub >= {c}) ? ({r}_sub + {c}) : {r}_sub;' )
    return r

#---------------------------------------------------------
# adder and subtractor are register values that can wrap
#---------------------------------------------------------
def adder( r, c, do_incr, init=0, incr=1, clk='', reset_='' ):
    if clk == '': clk = C.clk
    if reset_ == '': reset_ = C.reset_
    w = C.log2( c )
    reg( r, w )
    wrapped_add( f'{r}_p', w, r, incr, c )
    P(f'always @( posedge {clk} ) begin' )
    P(f'    if ( !{reset_} ) begin' )
    P(f'        {r} <= {init};' )
    P(f'    end else if ( {do_incr} ) begin' )
    P(f'        {r} <= {r}_p;' )
    P(f'    end' )
    P(f'end' )

def subtractor( r, c, do_decr, init=0, decr=1, clk='', reset_='' ):
    if clk == '': clk = C.clk
    if reset_ == '': reset_ = C.reset_
    w = C.log2( c )
    reg( r, w )
    wrapped_sub( f'{r}_p', w, r, decr, c )
    P(f'always @( posedge {clk} ) begin' )
    P(f'    if ( !{reset_} ) begin' )
    P(f'        {r} <= {i};' )
    P(f'    end else if ( {do_decr} ) begin' )
    P(f'        {r} <= {r}_p;' )
    P(f'    end' )
    P(f'end' )

#---------------------------------------------------------
# carry lookahead adder 
#---------------------------------------------------------
def cla( r, w, a, b, cin ):
    if ~C.custom_cla: 
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
# count leading zeroes/ones using priority encoder
#-------------------------------------------
def count_leading_zeroes( x, x_w ):
    cnt_w = C.value_bitwidth( x_w )
    reg( f'{x}_ldz', cnt_w )
    P(f'always @( {x} ) begin' )
    P(f'    casez( {x} )' )
    for i in range( x_w+1 ):
        case = f'{x_w}\'b'
        for k in range( i ): case += '0'
        if i != x_w: case += '1'
        for k in range( i+1, x_w ): case += '?'
        P(f'        {case}: {x}_ldz = {i};' )
    P(f'        default: {x}_ldz = 0;' )
    P(f'    endcase' )        
    P(f'end' )
    return f'{x}_ldz' 

def count_leading_ones( x, x_w ):
    cnt_w = C.value_bitwidth( x_w )
    reg( f'{x}_ldo', cnt_w )
    P(f'always @( {x} ) begin' )
    P(f'    casez( {x} )' )
    for i in range( x_w+1 ):
        case = f'{x_w}\'b'
        for k in range( i ): case += '1'
        if i != x_w: case += '0'
        for k in range( i+1, x_w ): case += '?'
        P(f'        {case}: {x}_ldo = {i};' )
    P(f'        default: {x}_ldo = 0;' )
    P(f'    endcase' )        
    P(f'end' )
    return f'{x}_ldo' 

#-------------------------------------------
# compute integer log2( x ) in hardware
#-------------------------------------------
def vlog2( x, x_w ):
    cnt_w = C.value_bitwidth( x_w )
    ldz = count_leading_zeroes( x, x_w )
    P(f'wire [{cnt_w-1}:0] {x}_lg2 = {cnt_w}\'d{x_w-1} - {ldz};' )
    
#-------------------------------------------
# choose eligible from mask and preferred 
#-------------------------------------------
def choose_eligible( r, elig_mask, cnt, preferred, clk='', reset_='' ):
    w = C.log2( cnt )
    prio_elig_mask = rotate_left( f'{r}_prio_elig_mask', cnt, preferred, elig_mask )
    chosen = count_leading_ones( prio_elig_mask, cnt )
    return wrapped_add( r, w, chosen, 1, cnt )

#-------------------------------------------
# For ROM, values must be decimal constants.
# The ROM can return multiple results.
# The maximum number of results to return is figured out automatically.
# The widths of the results are also figured out automatically.
# If values are missing, they are assumed to be 0.
#-------------------------------------------
def rom_1d( i0, names, entries, nesting=0 ):
    result_cnt = len( names )
    entry_cnt = len( entries )
    if not isinstance( entries[0], list ): 
        # normalize array
        new_entries = [ [entries[i]] for i in range( entry_cnt ) ]
        entries = new_entries
    i0_w = C.log2(entry_cnt)
    indent = ''
    for i in range( nesting ): indent += '    '
    if nesting == 0:
        result_max = [ 0 for i in range( result_cnt ) ]
        for entry in entries:
            for i in range( len( entry ) ):
                if entry[i] > result_max[i]: result_max[i] = entry[i]
        result_w = [ C.value_bitwidth(result_max[i]) for i in range( result_cnt ) ]
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
            P(f'{indent}    {i0_w}\'d{e}: {names[0]} = {v};' )
        else:
            P(f'{indent}    {i0_w}\'d{e}: begin' )
            for i in range( result_cnt ):
                v = entry[i] if i < len( entry ) else 0
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

def rom_2d( i0, i1, names, entries, nesting=0 ):
    result_cnt = len( names )
    entry_cnt = len( entries )
    if not isinstance( entries[0][0], list ): 
        # normalize array
        new_entries = []
        for i in range( entry_cnt ):
            new_entries.append( [ [entries[i][i1]] for i1 in range( len(entries[i]) ) ] )
        entries = new_entries
    i0_w = C.log2(entry_cnt)
    indent = ''
    for i in range( nesting ): indent += '    '
    if nesting == 0:
        result_max = [ 0 for i in range( result_cnt ) ]
        for i in range( entry_cnt ):
            for entry in entries[i]:
                for i in range( len( entry ) ):
                    if entry[i] > result_max[i]: result_max[i] = entry[i]
        result_w = [ C.value_bitwidth(result_max[i]) for i in range( result_cnt ) ]
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
        rom_1d( i1, names, entry, nesting+1 )
    P(f'{indent}    default: begin' )
    for i in range( result_cnt ):
        P(f'{indent}        {names[i]} = 0;' )
    P(f'{indent}        end' )
    P(f'{indent}    endcase' )

    if nesting == 0:
        P(f'end' )

# with p<n>_ prefixes
#
def pipe( p, sigs, pvld, prdy='' ):
    pp = p + 1
    reg( f'p{pp}_{pvld}', 1 )
    if prdy != '':
        wirea( f'p{p}_{prdy}', 1, f'p{pp}_{prdy}' )
    psigs = {}
    for sig in sigs:
        reg( f'p{pp}_{sig}', sigs[sig] )
        psigs[f'p{p}_{sig}'] = sigs[sig]
    P(f'always @( posedge {C.clk} ) begin' )
    P(f'    if ( !{C.reset_} ) begin' )
    P(f'        p{pp}_{pvld} <= 0;' )
    if prdy == '':
        P(f'    end else begin' )
    else:
        P(f'    end else if ( !p{pp}_{pvld} || p{pp}_{prdy} ) begin' )
    P(f'        p{pp}_{pvld} <= p{p}_{pvld};' )
    P(f'        if ( p{p}_{pvld} ) begin' )
    for sig in sigs:
        P(f'            p{pp}_{sig} <= p{p}_{sig};' )
    P(f'        end' )
    P(f'    end' )
    P(f'end' )
    if C.vdebug:
        dprint( f'p{p}', psigs, f'p{p}_{pvld}' )

# with arbitrary suffixes
#
def pipeS( osuff, isuff, sigs, pvld, prdy='' ):
    reg( f'{pvld}{osuff}', 1 )
    if prdy != '':
        wirea( f'{prdy}{isuff}', 1, f'{prdy}{osuff}' )
    for sig in sigs:
        reg( f'{sig}{osuff}', sigs[sig] )
    P(f'always @( posedge {C.clk} ) begin' )
    P(f'    if ( !{C.reset_} ) begin' )
    P(f'        {pvld}{osuff} <= 0;' )
    if prdy == '':
        P(f'    end else begin' )
    else:
        P(f'    end else if ( !{pvld}{osuff} || {pvld}{osuff} ) begin' )
    P(f'        {pvld}{osuff} <= {pvld}{isuff};' )
    P(f'        if ( {pvld}{isuff} ) begin' )
    for sig in sigs:
        P(f'            {sig}{osuff} <= {sig}{isuff};' )
    P(f'        end' )
    P(f'    end' )
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

    P(f'{name} {u_name}( .{C.clk}({C.clk}), .{C.reset_}({C.reset_}),' )
    P(f'                        .wr_pvld({pvld}), .wr_prdy({prdy}), .wr_pd('+'{'+f'{ins}'+'}),' )
    P(f'                        .rd_pvld({d_pvld}), .rd_prdy({d_prdy}), .rd_pd('+'{'+f'{outs}'+'}) );' )
    if with_wr_prdy:
        P(f'// synopsys translate_off' )
        P(f'always @( posedge {C.clk} ) begin' )
        P(f'    if ( {C.reset_} === 1 && {pvld} !== 0 && {prdy} !== 1 ) begin' )
        P(f'        $display( "%0d: %m: ERROR: fifo wr_pvld=%d but wr_prdy=%d", $stime, {pvld}, {prdy} );' )
        P(f'        $fatal;' )
        P(f'    end' )
        P(f'end' )
        P(f'// synopsys translate_on' )

def make_fifo( module_name ):
    info = fifos[module_name]
    P()
    P(f'module {module_name}( {C.clk}, {C.reset_}, wr_pvld, wr_prdy, wr_pd, rd_pvld, rd_prdy, rd_pd );' )
    P()
    input(  C.clk,       1 )
    input(  C.reset_,    1 )
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
        P(f'always @( posedge {C.clk} ) begin' )
        P(f'    rd_pvld <= wr_pvld;' )
        P(f'    if ( wr_pvld ) rd_pd <= wr_pd;' )
        P(f'end' )
    else:
        w     = info['w']
        a_w   = C.log2( depth )
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
        P(f'always @( posedge {C.clk} ) begin' )
        P(f'    if ( !{C.reset_} ) begin' )
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
        P(f'always @( posedge {C.clk} ) begin' )
        P(f'    if ( !{C.reset_} ) begin' )
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
        P(f'always @( posedge {C.clk} ) begin' )
        P(f'    if ( !{C.reset_} ) begin' )
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

def module_footer( mn ):
    P()
    P(f'endmodule // {mn}' )
    global fifos
    for fifo in fifos:
        make_fifo( fifo )
    fifos = {}

def tb_clk( decl_clk=True, default_cycles_max=2000, perf_op_first=100, perf_op_last=200 ):
    P(f'' )
    P(f'// {C.clk}' )
    P(f'//' )
    if decl_clk: P(f'reg  {C.clk};' )
    P(f'real {C.clk}_phase; ' )
    P(f'real {C.clk}_period; ' )
    P(f'real {C.clk}_half_period; ' )
    P(f'reg [31:0] cycle_cnt;' )
    P(f'reg [31:0] cycles_max;' )
    P(f'' )
    P(f'initial begin ' )
    P(f'    if ( !$value$plusargs( "{C.clk}_phase=%f", {C.clk}_phase ) ) begin ' )
    P(f'        {C.clk}_phase = 0.0; ' )
    P(f'    end ' )
    P(f'    if ( !$value$plusargs( "{C.clk}_period=%f", {C.clk}_period ) ) begin ' )
    P(f'        {C.clk}_period = 1.0; ' )
    P(f'    end ' )
    P(f'    if ( !$value$plusargs( "cycles_max=%f", cycles_max ) ) begin ' )
    P(f'        cycles_max = {default_cycles_max};' )
    P(f'    end ' )
    P(f'    {C.clk}_half_period = {C.clk}_period / 2.0; ' )
    P(f'    {C.clk} = 0; ' )
    P(f'    cycle_cnt = 0;' )
    P(f'    #({C.clk}_half_period); ' )
    P(f'    #({C.clk}_phase); ' )
    P(f'    fork ' )
    P(f'        forever {C.clk} = #({C.clk}_half_period) ~{C.clk}; ' )
    P(f'    join ' )
    P(f'end ' )
    P()
    P(f'always @( posedge {C.clk} ) begin' )
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
    P(f'// {C.reset_} ' )
    P(f'// ' )
    if decl_reset_: P(f'reg {C.reset_};' )
    P(f'initial begin ' )
    P(f'    {C.reset_} = 0; ' )
    P(f'    repeat( 10 ) @( posedge {C.clk} ); ' )
    P(f'    {C.reset_} <= 1; ' )
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
    P(f'// {C.clk}_rand_cycle_cnt' )
    P(f'//' )
    P(f'reg [31:0] {C.clk}_rand_cycle_cnt;' )
    P(f'initial begin' )
    P(f'    if ( !$value$plusargs( "{C.clk}_rand_cycle_cnt=%f", {C.clk}_rand_cycle_cnt ) ) begin ' )
    P(f'        {C.clk}_rand_cycle_cnt = {default_rand_cycle_cnt}; ' )
    P(f'    end ' )
    P(f'end' )

def tb_randbits( sig, _bit_cnt ):
    global seed_z_init, seed_w_init
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
        P(f'always @( posedge {C.clk} ) begin' )
        P(f'    if ( !{C.reset_} ) begin' )
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

def tb_randomize_sigs( sigs, pvld, cycle_cnt, prefix='rand' ):
    P()
    P(f'// randomize signals' )
    P(f'// For now, we let 50% of bits change each cycle (worst-case).' )
    P(f'//' )
    bit_cnt = 0;
    reg( pvld, 1 )
    for sig in sigs: 
        bit_cnt += sigs[sig]
        reg( sig, sigs[sig] )
    
    tb_randbits( f'{prefix}_bits', bit_cnt )

    P(f'reg [31:0] {prefix}_cnt;' )
    P(f'always @( posedge {C.clk} ) begin' )
    P(f'    if ( !{C.reset_} ) begin' )
    P(f'        {pvld} <= 0;' )
    P(f'        rand_cnt <= 0;' )
    P(f'    end else if ( {prefix}_cnt <= {cycle_cnt} ) begin' )
    P(f'        {pvld} <= {prefix}_cnt != 0;' )
    lsb = 0
    for sig in sigs:
        msb  = lsb + sigs[sig] - 1
        P(f'        {sig} <= rand_bits[{msb}:{lsb}];' )
        lsb  = msb + 1
    P(f'        {prefix}_cnt = {prefix}_cnt + 1;' )
    P(f'    end else begin' )
    P(f'        {pvld} <= 0;' )
    P(f'    end' )
    P(f'end' )
    P()
    dprint( prefix, sigs, pvld )

