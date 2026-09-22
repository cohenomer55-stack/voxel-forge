from __future__ import annotations
import gzip, struct
from typing import Any
TAG_END=0; TAG_BYTE=1; TAG_SHORT=2; TAG_INT=3; TAG_LONG=4; TAG_FLOAT=5; TAG_DOUBLE=6; TAG_BYTE_ARRAY=7; TAG_STRING=8; TAG_LIST=9; TAG_COMPOUND=10; TAG_INT_ARRAY=11; TAG_LONG_ARRAY=12
class Byte(int): pass
class Short(int): pass
class Int(int): pass
class Long(int): pass
class Float(float): pass
class Double(float): pass
class IntArray(list): pass
class LongArray(list): pass

def _u16(n:int)->bytes: return struct.pack('>H', n)
def _name(s:str)->bytes:
    b=s.encode('utf-8'); return _u16(len(b))+b

def tag_type(v:Any)->int:
    if isinstance(v,bool): return TAG_BYTE
    if isinstance(v,Byte): return TAG_BYTE
    if isinstance(v,Short): return TAG_SHORT
    if isinstance(v,Int): return TAG_INT
    if isinstance(v,Long): return TAG_LONG
    if isinstance(v,Float): return TAG_FLOAT
    if isinstance(v,Double): return TAG_DOUBLE
    if isinstance(v,int): return TAG_INT
    if isinstance(v,float): return TAG_DOUBLE
    if isinstance(v,str): return TAG_STRING
    if isinstance(v,(bytes,bytearray)): return TAG_BYTE_ARRAY
    if isinstance(v,IntArray): return TAG_INT_ARRAY
    if isinstance(v,LongArray): return TAG_LONG_ARRAY
    if isinstance(v,list): return TAG_LIST
    if isinstance(v,dict): return TAG_COMPOUND
    raise TypeError(type(v))

def payload(t:int,v:Any)->bytes:
    if t==TAG_BYTE: return struct.pack('>b',int(v))
    if t==TAG_SHORT: return struct.pack('>h',int(v))
    if t==TAG_INT: return struct.pack('>i',int(v))
    if t==TAG_LONG: return struct.pack('>q',int(v))
    if t==TAG_FLOAT: return struct.pack('>f',float(v))
    if t==TAG_DOUBLE: return struct.pack('>d',float(v))
    if t==TAG_STRING:
        b=v.encode('utf-8'); return _u16(len(b))+b
    if t==TAG_BYTE_ARRAY: return struct.pack('>i',len(v))+bytes(v)
    if t==TAG_INT_ARRAY: return struct.pack('>i',len(v))+b''.join(struct.pack('>i',int(x)) for x in v)
    if t==TAG_LONG_ARRAY: return struct.pack('>i',len(v))+b''.join(struct.pack('>q',int(x)) for x in v)
    if t==TAG_LIST:
        if not v: return bytes([TAG_END])+struct.pack('>i',0)
        types=[tag_type(x) for x in v]
        if len(set(types))!=1: raise TypeError(f'NBT list must be homogeneous: {types}')
        et=types[0]
        return bytes([et])+struct.pack('>i',len(v))+b''.join(payload(et,x) for x in v)
    if t==TAG_COMPOUND:
        out=bytearray()
        for k,val in v.items():
            tt=tag_type(val); out.append(tt); out.extend(_name(k)); out.extend(payload(tt,val))
        out.append(TAG_END); return bytes(out)
    if t==TAG_END: return b''
    raise TypeError(t)

def dumps(root:dict, root_name:str='Litematic')->bytes:
    return bytes([TAG_COMPOUND])+_name(root_name)+payload(TAG_COMPOUND,root)

def dump_gzip(root:dict,path:str,root_name:str='Litematic')->None:
    with gzip.open(path,'wb') as f: f.write(dumps(root,root_name))
