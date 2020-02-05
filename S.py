# S.py - common system functions used by scripts
#
import os
import subprocess
import re

def die( msg ):
    print( f'ERROR: {msg}' )
    sys.exit( 1 )

def cmd( c ):  
    info = subprocess.run( c, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    if info.returncode != 0: die( f'command failed: {c}' )
    return info.stdout

def match( s, pattern ): 
    return re.compile( pattern ).match( s )

def subst( s, pattern, subst ):
    return re.sub( pattern, subst, s )
