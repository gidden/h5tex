#!/usr/bin/python

from __future__ import print_function

import argparse as ap
import subprocess
from collections import namedtuple, defaultdict
import io
import re

from run_control import RunControl, NotSpecified, parse_rc

TypeInfo = namedtuple('TypeInfo', ['t', 'bytes'])

h5ts = {
    'H5T_IEEE_F64LE': TypeInfo('float', 8),
    'H5T_IEEE_F64BE': TypeInfo('float', 8),
    'H5T_IEEE_F32LE': TypeInfo('float', 4),
    'H5T_IEEE_F32BE': TypeInfo('float', 4),
    'H5T_STD_I64LE': TypeInfo('integer', 8),
    'H5T_STD_I64BE': TypeInfo('integer', 8),
    'H5T_STD_I32LE': TypeInfo('integer', 4),
    'H5T_STD_I32BE': TypeInfo('integer', 4),
    'H5T_STD_I16LE': TypeInfo('integer', 2),
    'H5T_STD_I16BE': TypeInfo('integer', 2),
    'H5T_STD_I8LE': TypeInfo('integer', 1),
    'H5T_STD_I8BE': TypeInfo('integer', 1),
    'H5T_STD_U64LE': TypeInfo('unsigned integer', 8),
    'H5T_STD_U64BE': TypeInfo('unsigned integer', 8),
    'H5T_STD_U32LE': TypeInfo('unsigned integer', 4),
    'H5T_STD_U32BE': TypeInfo('unsigned integer', 4),
    'H5T_STD_U16LE': TypeInfo('unsigned integer', 2),
    'H5T_STD_U16BE': TypeInfo('unsigned integer', 2),
    'H5T_STD_U8LE': TypeInfo('unsigned integer', 1),
    'H5T_STD_U8BE': TypeInfo('unsigned integer', 1),
    'H5T_STD_B8LE': TypeInfo('integer bitfield', 1),
    'H5T_STD_B8BE': TypeInfo('integer bitfield', 1),
    'H5T_STRING': 'string',
    'H5T_ARRAY': 'array',
}

tex_replace = {
    '_',
}

_tbl_template = """\\begin{{table}}[{options}]
\centering
\label{{{label}}}
\caption{{{caption}}}
\\begin{{tabular}}{{{layout}}}
\hline
{header}
{entries}
\end{{tabular}}
\end{{table}}
"""

def first_idx(x, lst):
    return lst.index(next(_ for _ in lst if x in _))

def all_idxs(x, lst):
    return [i for i, _ in enumerate(lst) if x in _]

def tex_clean(s):
    for x in tex_replace:
        s = s.replace(x, '\{0}'.format(x))
    return s

def read_type(x):
    name = x[-1].split("\"")[1]
    try:
        h5t = h5ts[x[0].strip().split()[0]]
    except KeyError:
        raise KeyError("H5T for {0} not supported. Line read: {1}".format(name, x))
    
    if h5t is 'array':
        x = x[0].split()
        h5t = h5ts[x[3]]
        n = x[2][1:-1]
        dtstr = '{0}-length array of {1}-byte {2}s'.format(n, h5t.bytes, h5t.t)
    elif h5t is 'string':
        h5t = TypeInfo(h5t, int(x[1].strip().split()[1][:-1]))
        dtstr = '{0}-character {1}'.format(h5t.bytes, h5t.t)    
    else:
        dtstr = '{0}-byte {1}'.format(h5t.bytes, h5t.t)
    return name, dtstr

def datasets(f):
    result = subprocess.check_output(['h5ls', '-r', f]).split('\n')
    return [x.split()[0] for x in result if 'Dataset' in x]

def insert_single_lines(idxs, l):
    # insert in the middle
    added = 0
    for i in range(1, len(idxs)):
        diff  = idxs[i][0] - idxs[i - 1][1] - 1
        if diff != 0:
            add = [(x, x) for x in range(idxs[i-1][1] + 1, idxs[i][0])]
            for x in reversed(add):
                idxs.insert(i + added, x)
            added += len(add)

    # insert in the front
    add = [(x, x) for x in range(idxs[0][0])]
    for x in reversed(add):
        idxs.insert(0, x)
    
    # insert in the back
    pos = len(idxs)
    add = [(x, x) for x in range(idxs[-1][1] + 1, l)]
    for x in reversed(add):
        idxs.insert(pos, x)

def datatypes(f, dataset):
    result = subprocess.check_output(['h5dump', '-d', dataset, f]).split('\n')
    typelines = result[
        first_idx('DATATYPE', result) + 1:first_idx('DATASPACE', result) - 1]
    idxs = zip(all_idxs('{', typelines), all_idxs('}', typelines))
    if len(idxs) > 0:
        insert_single_lines(idxs, len(typelines))
    typelines = [typelines[i:j + 1] for i, j in idxs]
    return [read_type(x) for x in typelines]

def gen_parser():
    p = ap.ArgumentParser("h5tex", add_help=True)
    
    h = "The HDF5 database to translate."
    p.add_argument('db', help=h)
    h = "A runcontrol file."
    p.add_argument('--rc', default=None, help=h)
    h = "The path to a specific dataset to print."
    p.add_argument('-d', '--dataset', default=None, help=h)
    h = "A latex table template file."
    p.add_argument('-t', '--template', default=None, help=h)
    h = "Print out debug statements."
    p.add_argument('--debug', action='store_true', default=False, help=h)
    h = "Skip datasets matching a pattern."
    p.add_argument('--skip', default=None, help=h)
    
    return p

def main():
    p = gen_parser()
    args = p.parse_args()
    
    db = args.db
    sets = [args.dataset] if args.dataset else datasets(db)
    rc = parse_rc(args.rc, default_nones=True) if args.rc else \
        RunControl(default_nones=True)
    if args.template:
        with io.open(args.template, 'r') as f:
            template = f.read()
    else:
        template = _tbl_template

    for s in sets:
        print(s)
        if args.skip and re.match(args.skip, s):
            print('skipping', s)
            continue
        if args.debug:
            print(s)
        name = s.split('/')[-1]
        options = rc.options or ''
        label = rc.label or 'tbl:{0}'
        caption = rc.caption or \
            'Datatype description of the {0} dataset.'
        layout = rc.layout or '|c|c|c|'
        header = rc.header or ("\\textbf{Name} & \\textbf{Data Type} "
                               "& \\textbf{Description}       \\\\ \\hline")
        entry_template = rc.entry_template or "{0} & {1} & {2} \\\\ \\hline\n"
        descriptions = rc.descriptions or defaultdict(str)
        entries = ''
        for col, dtstr in datatypes(db, s):
            entries += entry_template.format(tex_clean(col), 
                                             dtstr, tex_clean(descriptions[col]))
        tbl = template.format(options=options, 
                              label=label.format(name), 
                              caption=caption.format(name), 
                              layout=layout, 
                              header=header, 
                              entries=entries.strip())
        print()
        print(tbl)
        print()

if __name__ == '__main__':
    main()
