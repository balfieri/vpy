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
# S.py - common system functions used by scripts
#
import sys
import os
import os.path
import subprocess
import re

#-------------------------------------------
# Abort with message.
#-------------------------------------------
def die( msg ):
    print( f'ERROR: {msg}' )
    sys.exit( 1 )

#-------------------------------------------
# Run command with stderr mapped to stdout, die if it fails, then return stdout as string.
# Can have it just print what it would do by setting S.cmd_en = False.
#-------------------------------------------
cmd_en = True

def cmd( c, echo=True, echo_stdout=False, can_die=True ):  
    if echo: print( c )
    if cmd_en:
        info = subprocess.run( c, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
        if echo_stdout: print( info.stdout )
        if can_die and info.returncode != 0: die( f'command failed: {c}' )
        return info.stdout
    else:
        return ''

#-------------------------------------------
# Use these shortcuts if you prefer PERL ordering of args (e.g., s ~= /pattern/).
#
# match() returns matching info.
#
# substr() returns string after substitutions. 'subst' may contain references to matches,
# such as \1.
#-------------------------------------------
def match( s, pattern ): 
    return re.compile( pattern ).match( s )

def subst( s, pattern, subst ):
    return re.sub( pattern, subst, s )

#-------------------------------------------
# Return True if file exists
#-------------------------------------------
def file_exists( file_name ):
    try:
        with open( file_name ) as f:
            return True
    except FileNotFoundError:
        return False

#-------------------------------------------
# Get number of lines in a file
#-------------------------------------------
def file_line_cnt( file_name ):
    if not os.path.exists( file_name ): die( f'file not found: {file_name}' )
    with open( file_name ) as my_file:
        line_cnt = sum( 1 for _ in my_file )
    return line_cnt

#-------------------------------------------
# Apply edits to a file
#-------------------------------------------
def file_edit( file_name, edits, echo_edits=False , must_apply_all=True ):
    if not file_exists( file_name ): die( f'file_edit: {file_name} does not exist' )
    edit_applied = { patt: False for patt in edits }
    cmd( f'rm -f {file_name}.tmp' )
    out_file = open( f'{file_name}.tmp', 'w' )
    with open( file_name ) as in_file:
        for line in in_file:
            for patt in edits:
                if match( line, patt ):
                    line = subst( line, patt, edits[patt] ) 
                    if echo_edits: print( f'{file_name}: {line}', end='' )
                    edit_applied[patt] = True
            out_file.write( line )
    out_file.close()
    if must_apply_all:
        for patt in edit_applied:
            if not edit_applied[patt]: die( f'file_edit: this pattern was never applied to {file_name}: {patt}' )
    cmd( f'mv {file_name}.tmp {file_name}' )
