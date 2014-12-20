from __future__ import print_function

import argparse as ap
import subprocess

TypeInfo = namedtuple('TypeInfo', ['t', 'bytes'], verbose=True)

h5ts = {
    'H5T_IEEE_F64LE': TypeInfo('float', 8),
    'H5T_IEEE_F64BE': TypeInfo('float', 8),
    'H5T_IEEE_F32LE': TypeInfo('float', 4),
    'H5T_IEEE_F32BE': TypeInfo('float', 4),
    'H5T_STD_I64LE': TypeInfo('int', 8),
    'H5T_STD_I64BE': TypeInfo('int', 8),
    'H5T_STD_I32LE': TypeInfo('int', 4),
    'H5T_STD_I32BE': TypeInfo('int', 4),
    'H5T_STD_I16LE': TypeInfo('int', 2),
    'H5T_STD_I16BE': TypeInfo('int', 2),
    'H5T_STRING': 'string',
}

def first_idx(x, lst):
    return lst.index(next(_ for _ in res if x in _))

def all_idxs(x, lst):
    return [i for i, _ in enumerate(lst) if x in _]

def read_type(x):
    h5t = h5ts[x[0].strip().split()[0]]
    if not isinstance(h5t, TypeInfo):
        h5t = TypeInfo(h5t, int(x[1].strip().split()[:-1]))
    name = x[-1].split("\"")[1]
    return name, h5t.t, h5t.bytes

def datasets(f):
    result = subprocess.check_output(['h5ls', '-r', f]).split('\n')
    return [x.split()[0] for x in result if 'Dataset' in x]

def datatypes(f, dataset):
    result = subprocess.check_output(['h5dump', '-d', dataset, f]).split('\n')
    typelines = result[
        first_idx('DATATYPE', result) + 1:find_idx('DATASPACE', result) - 1]
    idxs = [-1] + all_idxs('}', typelines)
    typelines = [typelines[idxs[i] + 1:idxs[i+1] + 1] for i in range(idxs) - 1]
    return [read_type(x) for x in typelines]

def gen_parser():
    p = ap.ArgumentParser("h5tex", add_help=True)
    
    dbh = "The HDF5 database to translate."
    p.add_argument('db', help=dbh)
    
    return p

def main():
    p = gen_parser()
    args = p.parse_args()
    
    with io.open(args.template, 'r') as f:
        template = f.read()
    db = args.db
    sets = datasets(db)
    for s in sets:
        name = s.split('/')[-1]
        options = args.options or ''
        label = info.label or 'tbl:{0}'
        label = label.format(name)
        caption = info.caption or 'Datatype description of the {0} dataset.'
        caption = caption.format(name)
        layout = info.layout or '|c|c|c', 
        header = info.header or "\textbf{Name} & \textbf{Data Type} & \textbf{Description}       \\ \hline"
        entry_template = "{0} & {1} & {2} \\ \hline\n"
        entries = ''
        for dtypes in datatypes(s, db):
            name, dt, nbytes = dtype            
            entries += entry_template.format(name, 
                                             '{0}-byte {1}'.format(nbytes, dt), 
                                             info.descriptions[name])
        tbl = template.format(options=options, 
                              label=label, 
                              caption=caption, 
                              layout=layout, 
                              header=header, 
                              entries=entries)
        print(tbl)


if __name__ == '__main__':
    main()
