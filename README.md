V.py is a Python module that has various helper functions to generate common Verilog logic structures.
For now, you'll need to read the comments in V.py to see what is available.

S.py is a Python module that has a few system helper functions unrelated to Verilog.

There are also some higher-level generators and that sit above V.py. They generate designs 
as well as corresponding testbenches. Specific functions and params are described down below.

* fifo.py - fifo generator
* cache.py - cache generator

# Examples

The following examples are provided. Each has an associated testbench around it. So if the design is
in foo.py, the generated files will be foo.v (design) and tb_foo.v (testbench):

* arb_rr.py   - round-robin arbiter (combinational)
* fifo1.py    - stallable fifo with ram in flops
* cache1.py   - L0 read-only non-blocking cache with tags and data in flops 

To build all examples using the canonical Makefile and gen.py script, type:

<pre>
make
</pre>

Assuming you have Icarus Verilog installed (iverilog), to run all examples with a .vcd dump, 
which uses the vsim.py script, type:

<pre>
make dtest
</pre>

I use a Makefile and gen.py outer script to generate either the DUT or the testbench. 
This is my convention, not required.

The examples all use a configuration file, C.py, that parameterizes the example designs. 
Again, this is my convention, not required.

So each design will typically do this at the beginning:

<pre>
import S                # system utility functions
import V                # the guts of VPY
import C                # conventional config file
...
</pre>

# S.py Functions

These are system-level functions that do not involved Verilog.

```python
def die( msg )
def cmd( c, echo=True, echo_stdout=False, can_die=True )
def match( s, pattern )
def subst( s, pattern, subst )
def file_exists( file_name )
def file_line_cnt( file_name )
def file_edit( file_name, edits, echo_edits=False , must_apply_all=True )
```

# V.py Functions

These are low-level functions involved with Verilog generation.

## Initialization

```python
def reinit( _clk='clk', _reset_='reset_', _vdebug=True, _vassert=True, _ramgen_cmd='' )
```

## Static Sizes and Widths

```python
def log2( n )
def is_pow2( n )
def value_bitwidth( n )
```

## Declarations

```python
def module_header_begin( mn )
def decl( kind, name, w, is_io=False )     
def decla( kind, name, w, v )
def input( name, w )      
def sinput( name, w )     
def output( name, w )     
def soutput( name, w )    
def wire( name, w )
def wirea( name, w, v )
def swire( name, w )  
def swirea( name, w, v )
def reg( name, w )
def sreg( name, w )
def enum( prefix, names )
def parse_enums( file_name, prefix )
def module_header_end()
def module_footer( mn )
```

## Debug

```python
def display( msg, sigs, use_hex_w=16, prefix='        ', show_module=False )
def dprint( msg, sigs, pvld, use_hex_w=16, with_clk=True, indent='' )
def dassert( expr, msg, pvld='', with_clk=True, indent='    ', if_fatal='' )
def dassert_no_x( expr, pvld='', with_clk=True, indent='    ', if_fatal='' )
```

## Miscellaneous

```python
def always_at_posedge( stmt='begin', _clk='' )
```

## Interfaces

```python
def iface_width( sigs )
def iface_decl( kind, name, sigs, is_io=False, stallable=True )
def iface_input( name, sigs, stallable=True )
def iface_output( name, sigs, stallable=True )
def iface_wire( name, sigs, is_io=False, stallable=True )
def iface_reg( name, sigs, is_io=False, stallable=True )
def iface_reg_array( name, cnt, is_io=False, stallable=True, suff='_' )
def iface_reg_assign( lname, rname, sigs, indent='        ' )
def iface_inst( pname, wname, sigs, is_io=False, stallable=True )
def iface_concat( iname, sigs, r='' )
def iface_unconcat( cname, sigs, oname='' )
def iface_combine( iname, oname, sigs, do_decl=True )
def iface_split( iname, oname, sigs, do_decl=True )
def iface_stage( iname, oname, sigs, pvld, prdy='', full_handshake=False, do_dprint=True )
def iface_stageN( p, sigs, pvld, prdy='' )
def iface_dprint( name, sigs, pvld, prdy='', use_hex_w=16, with_clk=True, indent='' )
```

## Concatenation

```python
def repl( expr, cnt )
def reverse( bits, w, rbits='' )
def concata( vals, w, r='', reverse=True )
def unconcata( combined, cnt, w, r='', reverse=True )
```

## Muxing and Shifting

```python
def muxa( r, w, sel, vals, add_reg=True )
def muxr( r, w, sel, add_reg, *vals )
def mux( r, w, sel, *vals )
def mux_subword( r, subword_w, sel, word, word_w, stride=0, lsb=0, add_reg=True )
def muxN( sigs, sel, vals, add_reg=True )
def rotate_left( r, w, n, bits )
def rotate_right( r, w, n, bits )
def collapse( mask, mask_w, r, vals={}, gen_indexes=True )
def uncollapse( mask, indexes, index_cnt, vals, r )
```

## Integer Math

```python
def wrapped_add( r, w, a, b, c )
def wrapped_sub( r, w, a, b, c )
def adder( r, c, do_incr, init=0, incr=1, _clk='', _reset_='' )
def subtractor( r, c, do_decr, init=0, decr=1, _clk='', _reset_='' )
def cla( r, w, a, b, cin )
def vlog2( x, x_w )
def hash( x, x_w, r_w, r='' )
```

## Fixed-Point Math

```python
def fp_resize( fp1, r, is_signed, int1_w, frac1_w, intr_w, fracr_w )
def fp_lsha( fp1, sel, lshs, r, is_signed, int1_w, frac1_w, intr_w, fracr_w )
def fp_lsh( fp1, lsh, lsh_max, r, is_signed, int1_w, frac1_w, intr_w, fracr_w )
def fp_mul( fp1, fp2, r, is_signed, int1_w, frac1_w, int2_w=-1, frac2_w=-1, intr_w=-1, fracr_w=-1, extra_lsh='', extra_lsh_max=0 )
```

## LogN-Tree-Based Logic

```python
def count_zeroes( x, x_w, r='' )
def count_ones( x, x_w, r='' )
def count_leading_zeroes( x, x_w, add_reg=True, suff='_ldz' )
def count_leading_ones( x, x_w, add_reg=True, suff='_ldo' )
def is_one_hot( mask, mask_w, r='' )
def binary_to_one_hot( b, mask_w, r='', pvld='' )
def one_hot_to_binary( mask, mask_w, r, r_any_vld='' )
def collapse( mask, mask_w, r, vals={}, gen_indexes=True )
def uncollapse( mask, indexes, index_cnt, vals, r )
```

## Arbiters

```python
def choose_eligible( r, elig_mask, cnt, preferred, gen_preferred=False, adv_preferred='' )
def choose_eligible_with_highest_prio( r, vlds, prios, prio_w )
def choose_eligibles( r, elig_mask, elig_cnt, preferred, req_mask, req_cnt, gen_preferred=False )
def resource_accounting( name, cnt, add_free_cnt=False, set_i_is_free_i=False )
```

## Storage Structures

```python
def rom_1d( i0, names, entries, nesting=0, result_w=None )
def rom_2d( i0, i1, names, entries, nesting=0, result_w=None )
def ram( iname, oname, sigs, depth, wr_cnt=1, rd_cnt=1, rw_cnt=0, clks=[], m_name='', u_name='', add_blank_line=True )
```

## Testbenches

```python
def tb_clk( decl_clk=True, default_cycles_max=2000, perf_op_first=100, perf_op_last=200 )
def tb_reset_( decl_reset_=True )
def tb_dump( module_name )
def tb_rand_init( default_rand_cycle_cnt=300 )
def tb_randbits( sig, _bit_cnt )
def tb_randomize_sigs( sigs, pvld, prdy='', cycle_cnt='', prefix='' )
def tb_ram_decl( ram_name, d, sigs )
def tb_ram_file( ram_name, file_name, sigs, is_hex_data=True )
def tb_ram_read( ram_name, row, oname, sigs, do_decl=True )
def tb_ram_write( ram_name, row, iname, sigs, do_decl=True )
```

# Generators

By convention, each generator takes a set of parameters in the form of a Python dictionary. For each generator that follows, the required
and optional params are described first.

## fifo.py - fifo generator

```python
params = { 
    # required always:
    'd':                 <depth>,       # fifo depth of ram (does not include any in/out registering)

    # optional for stage(), required for other functions:
    'w':                 <width>,       # stage() derives it from sigs
    'm_name':            <module_name>, # stage() derives it from fifo params

    # optional (default values are shown)
    'is_async':          False,         # is an asynchronous fifo?
    'wr_clk':            V.clk,         # write-side clock name
    'wr_reset_':         V.reset_,      # write-side reset-low name
    'wr':                'wr',          # write-side iface name
    'rd_clk':            V.clk,         # read-side clock name (may differ only if is_async=True)
    'rd_reset_':         V.reset_,      # read-side clock name (may differ only if is_async=True)
    'rd':                'rd'           # read-side iface name
    }
```

This causes a fifo stage to get inserted inside the current module. In reality, a fifo module is instantiated at the current location, 
then the fifo module itself will get generated at the end of the current module:

```python
def stage( params, iname, oname, sigs, pvld='pvld', prdy='prdy', inst_name='', with_wr_prdy=True )
```

These generate a fifo module or a corresponding testbench module, and should not be called from inside a module. If you always use stage(),
you need not call these. They are mainly for fifo testing and for those who want the fifo module in a separate file:

```python
def make( params )
def make_tb( name, params )
```

This can be used to instantiate an existing fifo module (if it was generated using make()):

```python
def inst( params, inst_name, iname, oname, sigs, pvld='pvld', prdy='prdy', with_wr_prdy=True, do_decl=True, do_dprint=False )
```

## cache.py - cache generator

```python
params = { 
    # required:
    'line_cnt':      <count>            # number of lines in the cache
    'assoc':         <associativity>    # ways per set (if line_cnt, then it's fully associative)
    'line_w':        <bitwidth>,        # width of line (dat)
    'req_id_w':      <bitwidth>,        # width of req_id in request
    'req_addr_w':    <bitwidth>,        # width of virtual address in request
 
    # optional:
    'is_read_only':  True,              # read-only cache?
    'cache_name':    'cache',           # short name used in interfaces for cache itself
    'unit_name':     'unit',            # short name used in interfaces for unit using the cache
    'mem_name':      'mem',             # short name used in interfaces for memory subsystem
    'ref_cnt_max':   1,                 # max reference count per line
    'tag_ram_kind':  'ra2',             # tag ram kind: ra2 or ff (default is ff for fully-associative)
    'data_ram_kind': 'ra2',             # data ram kind: ra2 or ff
    'req_cnt':       1,                 # number of request interfaces
    'mem_dat_w':     <line_w>,          # memory width (must be a integer multiple of line_w)
    'tb_addr_cnt':   <req_id_cnt/2>,    # for generated testbench, number of unique addresses to use in requests
    }
```

These generate a cache module or a corresponding testbench module, and should not be called from inside a module:

```python
def make( params )
def make_tb( name, params )
```

This can be used to instantiate an existing cache module. Because caches involve a lot of interfaces, it make sense to call inst() to get
all the interface wires generated before using any interface:

```python
def inst( params, inst_name, do_dprint=False )
```

The following cache components get inserted inside the current module. Normally, one does not use these directly, 
but they are provided for the rare cases where one would want to use them for a custom cache not supported by the generator:

```python
def tags( name, addr_w, tag_cnt, req_cnt, ref_cnt_max, incr_ref_cnt_max=1, decr_req_cnt=0, can_always_alloc=False, custom_avails=False )
```

# Things To Do

* Add xbar.py generator
* Add float.py generator

Bob Alfieri<br>
Chapel Hill, NC
