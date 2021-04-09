V.py is a Python module that has various helper functions to generate common Verilog logic structures.
For now, you'll need to read the comments in V.py to see what is available.

S.py is a Python module that has a few system helper functions unrelated to Verilog.


<pre>
import S
import V
 
V.reinit()
...
</pre>

# Available Functions

You can find more detailed explanations in the comment blocks above the functions in V.py. Here's a brief summary of the functions available and their categories.

## Initialization

```python
def reinit( _clk='clk', _reset_='reset_', _vdebug=True, _vassert=True ):
```

## Static Sizes and Widths

```python
def log2( n ):
def is_pow2( n ):
def value_bitwidth( n ):
```

## Declarations

```python
def module_header_begin( mn ):
def decl( kind, name, w, is_io=False ):     
def decla( kind, name, w, v ):
def input( name, w ):      
def sinput( name, w ):     
def output( name, w ):     
def soutput( name, w ):    
def wire( name, w ):       decl( 'wire', name, w )
def wirea( name, w, v ):   decla( 'wire', name, w, v )
def swire( name, w ):      decl( 'wire signed', name, w )
def swirea( name, w, v ):  decla( 'wire signed', name, w, v )
def reg( name, w ):        decl( 'reg', name, w )
def sreg( name, w ):       decl( 'reg signed', name, w )
def enum( prefix, names ):
def parse_enums( file_name, prefix ):
def module_header_end():
def module_footer( mn ):
```

## Debug

```python
def display( msg, sigs, use_hex_w=16, prefix='        ' ):
def dprint( msg, sigs, pvld, use_hex_w=16, with_clk=True, indent='' ):
def dassert( expr, msg, pvld='', with_clk=True, indent='    ' ):
def dassert_no_x( expr, pvld='', with_clk=True, indent='    ' ):
```

## Miscellaneous

```python
def always_at_posedge( _clk='' ):
```

## Interfaces

```python
def iface_width( sigs ):
def iface_decl( kind, name, sigs, is_io=False, stallable=True ):
def iface_input( name, sigs, stallable=True ):
def iface_output( name, sigs, stallable=True ):
def iface_wire( name, sigs, is_io=False, stallable=True ):
def iface_reg( name, sigs, is_io=False, stallable=True ):
def iface_reg_assign( lname, rname, sigs, indent='        ' ):
def iface_inst( pname, wname, sigs, is_io=False, stallable=True ):
def iface_concat( iname, sigs ):
def iface_combine( iname, oname, sigs, do_decl=True ):
def iface_split( iname, oname, sigs, do_decl=True ):
def iface_stage( iname, oname, sigs, pvld, prdy='', full_handshake=False, do_dprint=True ):
def iface_stageN( p, sigs, pvld, prdy='' ):
def iface_dprint( name, sigs, pvld, prdy='', use_hex_w=16, with_clk=True, indent='' ):
```

## Concatenation

```python
def repl( expr, cnt ):
def reverse( bits, w, rbits='' ):
def concata( vals, w, r='', reverse=True ):
def unconcata( combined, cnt, w, r='', reverse=True ):
```

## Muxing and Shifting

```python
def muxa( r, w, sel, vals, add_reg=True ):
def muxr( r, w, sel, add_reg, *vals ):
def mux( r, w, sel, *vals ):
def mux_subword( r, subword_w, sel, word, word_w, stride=0, lsb=0, add_reg=True ):
def muxN( sigs, sel, vals, add_reg=True ):
def rotate_left( r, w, n, bits ):
def rotate_right( r, w, n, bits ):
def collapse( mask, mask_w, r, vals={}, gen_indexes=True ):
def uncollapse( mask, indexes, index_cnt, vals, r ):
```

## Integer Math

```python
def wrapped_add( r, w, a, b, c ):
def wrapped_sub( r, w, a, b, c ):
def adder( r, c, do_incr, init=0, incr=1, _clk='', _reset_='' ):
def subtractor( r, c, do_decr, init=0, decr=1, _clk='', _reset_='' ):
def cla( r, w, a, b, cin ):
def vlog2( x, x_w ):
```

## Fixed-Point Math

```python
def fp_resize( fp1, r, is_signed, int1_w, frac1_w, intr_w, fracr_w ):
def fp_lsha( fp1, sel, lshs, r, is_signed, int1_w, frac1_w, intr_w, fracr_w ):
def fp_lsh( fp1, lsh, lsh_max, r, is_signed, int1_w, frac1_w, intr_w, fracr_w ):
def fp_mul( fp1, fp2, r, is_signed, int1_w, frac1_w, int2_w=-1, frac2_w=-1, intr_w=-1, fracr_w=-1, extra_lsh='', extra_lsh_max=0 ):
```

## LogN-Tree-Based Logic

```python
def count_zeroes( x, x_w, r='' ):
def count_ones( x, x_w, r='' ):
def count_leading_zeroes( x, x_w, add_reg=True, suff='_ldz' ):
def count_leading_ones( x, x_w, add_reg=True, suff='_ldo' ):
def is_one_hot( mask, mask_w, r='' ):
def binary_to_one_hot( b, mask_w, r='', pvld='' ):
def one_hot_to_binary( mask, mask_w, r, r_any_vld='' ):
def collapse( mask, mask_w, r, vals={}, gen_indexes=True ):
def uncollapse( mask, indexes, index_cnt, vals, r ):
```

## Arbiters

```python
def choose_eligible( r, elig_mask, cnt, preferred, gen_preferred=False, adv_preferred='' ):
def choose_eligible_with_highest_prio( r, vlds, prios, prio_w ):
def choose_eligibles( r, elig_mask, elig_cnt, preferred, req_mask, req_cnt, gen_preferred=False ):
def resource_accounting( name, cnt, add_free_cnt=False, set_i_is_free_i=False ):
```

## Storage Structures

```python
def rom_1d( i0, names, entries, nesting=0, result_w=None ):
def rom_2d( i0, i1, names, entries, nesting=0, result_w=None ):
def fifo( sigs, pvld, prdy, depth, with_wr_prdy=True, prefix='d_', u_name='' ):
def cache_tags( name, addr_w, tag_cnt, req_cnt, ref_cnt_max, incr_ref_cnt_max=1, decr_req_cnt=0, can_always_alloc=False ):
def cache_filled_check( name, tag_i, r, tag_cnt, add_reg=True ):
```

## Testbenches

```python
def tb_clk( decl_clk=True, default_cycles_max=2000, perf_op_first=100, perf_op_last=200 ):
def tb_reset_( decl_reset_=True ):
def tb_dump( module_name ):
def tb_rand_init( default_rand_cycle_cnt=300 ):
def tb_randbits( sig, _bit_cnt ):
def tb_randomize_sigs( sigs, pvld, prdy='', cycle_cnt='', prefix='' ):
def tb_ram_decl( ram_name, d, sigs ):
def tb_ram_file( ram_name, file_name, sigs, is_hex_data=True ):
def tb_ram_read( ram_name, row, oname, sigs, do_decl=True ):
def tb_ram_write( ram_name, row, iname, sigs, do_decl=True ):
```
