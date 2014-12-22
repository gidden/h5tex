from collections import defaultdict

iddescr = "The hex value of a UUID"

descriptions = defaultdict(str, {
'instid': iddescr + ' for an NFCTP graph instance.',
'id': 'A uniquely identifying value.',
'arcid': iddescr + ' for an arc.',
'caps': 'Capacity RHS values.',
'cap_dirs': 'Whether a constraint is greater or less-than',
'paramid': iddescr + ' for a point in parameter space.',
'species': 'A description of a problem species.',
'n_arcs': 'The number of arcs in an NFCTP instance.',
'n_u_grps': 'The number of supply groups in an NFCTP instance.',
'n_v_grps': 'The number of demand groups in an NFCTP instance.',
'n_u_nodes': 'The number of supply nodes in an NFCTP instance.',
'n_v_nodes': 'The number of demand nodes in an NFCTP instance.',
'n_constrs': 'The number of constraints in an NFCTP instance.',
'excl_frac': 'The fraction of arcs in a NFCTP graph that are exclusive.',
'solnid': iddescr + ' for a solution to an ExchangeGraph instance.',
'cyclus_version': 'The version of Cyclus used to generate a solution.',
'gid': 'A unique value identifying an ExchangeGroup',
'kind': 'Whether an object is associated with supply or demand.',
'qty': 'A quantity.',
'excl': 'Whether or not an arc is exclusive.',
'excl_id': 'A unique value identifying the mutually exclusive group an arc belongs to.',
'solver': 'A description of the solver used.',
'problem': 'A description of the problem family.',
'time': 'How long a solution took.',
'objective': 'The objective value associated with a solution.',
'cyclopts_version': 'The version of Cyclopts used to generate a solution.',
'timestamp': 'A timestamp of when a solution was ran.',
'pref_flow': 'The value of the product of preference and flow for arcs.',
})

