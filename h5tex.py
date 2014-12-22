#!/usr/bin/python

from __future__ import print_function

import argparse as ap
import subprocess
from collections import namedtuple, defaultdict
import io

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
    'H5T_STD_B8LE': TypeInfo('integer bitfield', 1),
    'H5T_STD_B8BE': TypeInfo('integer bitfield', 1),
    'H5T_STRING': 'string',
    'H5T_ARRAY': 'array',
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

class NotSpecified(object):
    """A helper class singleton for run control meaning that a 'real' value
    has not been given."""
    def __repr__(self):
        return "NotSpecified"

NotSpecified = NotSpecified()

#
# Run Control
#
# Code basis taken from xdress' run control in xdress/utils.py.
#  
class RunControl(object):
    """A composable configuration class for cyclopts. Unlike argparse.Namespace,
    this keeps the object dictionary (__dict__) separate from the run control
    attributes dictionary (_dict). Modified from xdress' run control in
    xdress/utils.py"""

    def __init__(self, default_nones=False, **kwargs):
        """Parameters
        -------------
        kwargs : optional
            Items to place into run control.
        default_nones : bool
            a flag denoting that default values should be accessible by Nones

        """
        self._dict = {}
        self._nones = default_nones
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._updaters = {}

    def __getattr__(self, key):
        if key in self._dict:
            return self._dict[key]
        elif key in self.__dict__:
            return self.__dict__[key]
        elif key in self.__class__.__dict__:
            return self.__class__.__dict__[key]
        elif self._nones:
            return None
        else:
            msg = "RunControl object has no attribute {0!r}.".format(key)
            raise AttributeError(msg)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            if value is NotSpecified and key in self:
                return
            self._dict[key] = value

    def __delattr__(self, key):
        if key in self._dict:
            del self._dict[key]
        elif key in self.__dict__:
            del self.__dict__[key]
        elif key in self.__class__.__dict__:
            del self.__class__.__dict__[key]
        else:
            msg = "RunControl object has no attribute {0!r}.".format(key)
            raise AttributeError(msg)

    def __iter__(self):
        return iter(self._dict)

    def __repr__(self):
        keys = sorted(self._dict.keys())
        s = ", ".join(["{0!s}={1!r}".format(k, self._dict[k]) for k in keys])
        return "{0}({1})".format(self.__class__.__name__, s)

    def _pformat(self):
        keys = sorted(self._dict.keys())
        f = lambda k: "{0!s}={1}".format(k, pformat(self._dict[k], indent=2))
        s = ",\n ".join(map(f, keys))
        return "{0}({1})".format(self.__class__.__name__, s)

    def __contains__(self, key):
        return key in self._dict or key in self.__dict__ or \
                                    key in self.__class__.__dict__

    def __eq__(self, other):
        if hasattr(other, '_dict'):
            return self._dict == other._dict
        elif isinstance(other, Mapping):
            return self._dict == other
        else:
            return NotImplemented

    def __ne__(self, other):
        if hasattr(other, '_dict'):
            return self._dict != other._dict
        elif isinstance(other, Mapping):
            return self._dict != other
        else:
            return NotImplemented

    def _update(self, other):
        """Updates the rc with values from another mapping.  If this rc has
        if a key is in self, other, and self._updaters, then the updaters
        value is called to perform the update.  This function should return
        a copy to be safe and not update in-place.
        """
        if hasattr(other, '_dict'):
            other = other._dict
        elif not hasattr(other, 'items'):
            other = dict(other)
        for k, v in other.items():
            if v is NotSpecified:
                pass
            elif k in self._updaters and k in self:
                v = self._updaters[k](getattr(self, k), v)
            setattr(self, k, v)

def parse_rc(files, default=False):
    """Parse a list of rc files.

    Parameters
    ----------
    files : list or str
        the files to parse
    default : bool
        a flag denoting that default values should be accessible by Nones

    Returns
    -------
    rc : RunControl
    """
    files = [files] if isinstance(files, basestring) else files
    rc = RunControl(default=default)
    for rcfile in files:
        if not os.path.isfile(rcfile):
            continue
        rcdict = {}
        exec_file(rcfile, rcdict, rcdict)
        rc._update(rcdict)
    return rc

def exec_file(filename, glb=None, loc=None):
    """A function equivalent to the Python 2.x execfile statement. Taken from
    xdress/utils.py"""
    with io.open(filename, 'r') as f:
        src = f.read()
    exec(compile(src, filename, "exec"), glb, loc)

def first_idx(x, lst):
    return lst.index(next(_ for _ in lst if x in _))

def all_idxs(x, lst):
    return [i for i, _ in enumerate(lst) if x in _]

def read_type(x):
    name = x[-1].split("\"")[1]
    try:
        h5t = h5ts[x[0].strip().split()[0]]
    except KeyError:
        raise KeyError("H5T for {0} not supported. Line read: {1}".format(name, x))
    
    if h5t is 'array':
        print(x)
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
        for name, dtstr in datatypes(db, s):
            entries += entry_template.format(name, dtstr, descriptions[name])
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
