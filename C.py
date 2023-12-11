# C.py - global configuration options specific to our designs
#
import sys
import math
import S
import V

P = print

def reinit():
    global addr_w, mem_addr_w, mem_dat_w
    global l0c_slot_cnt, l0c_slot_id_w, l0c_line_w, l0c_req_id_w, l0c_req_id_cnt
    global l0c_addr_w, l0c_dat_w, l0c_ref_cnt_max, l0c_subword_w, l0c_subword_cnt, l0c_mem_tag_id_w
    global xx2l0c, l0c2xx_status, l0c2xx_dat, l0c2mem, mem2l0c
    global l0c_tb_addr_cnt, l0c_tb_addr_id_w

    # VERILOG
    #
    V.reinit( 'lclk', 'lreset_', _ramgen_cmd='./bramgen' )

    addr_w            = 32              # bits per virtual byte address
    mem_dat_w         = 64              # 8B for now
    mem_addr_w        = addr_w - V.log2( mem_dat_w >> 3 )

    #-------------------------------------------------------
    # L0
    #-------------------------------------------------------
    l0c_slot_cnt              = 2
    l0c_slot_id_w             = V.log2( l0c_slot_cnt )
    l0c_line_w                = 32
    l0c_dat_w                 = l0c_line_w
    l0c_req_id_w              = 3
    l0c_req_id_cnt            = 1 << l0c_req_id_w
    l0c_addr_w                = addr_w - V.log2( l0c_dat_w >> 3 )
    l0c_ref_cnt_max           = 4
    l0c_subword_w             = l0c_addr_w - mem_addr_w
    l0c_subword_cnt           = 1 << l0c_subword_w
    l0c_mem_tag_id_w          = l0c_req_id_w + l0c_subword_w + l0c_slot_id_w
    l0c_tb_addr_cnt           = l0c_req_id_cnt >> 1
    l0c_tb_addr_id_w          = V.log2( l0c_tb_addr_cnt )

    xx2l0c                    = { 'req_id':             l0c_req_id_w,
                                  'addr':               l0c_addr_w }

    l0c2xx_status             = { 'req_id':             l0c_req_id_w,
                                  'is_hit':             1,                      # returning data soon
                                  'is_miss':            1,
                                  'must_retry':         1 }                     # hit-under-miss or can't allocate -> punt to client
    l0c2xx_dat                = { 'req_id':             l0c_req_id_w,
                                  'dat':                l0c_dat_w }

    l0c2mem                   = { 'tag_id':             l0c_mem_tag_id_w,
                                  'addr':               mem_addr_w }

    mem2l0c                   = { 'tag_id':             l0c_mem_tag_id_w,
                                  'dat':                mem_dat_w }
