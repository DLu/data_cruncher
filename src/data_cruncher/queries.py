from .base import run_query


def matches_property(prop_s, value_s, entity_value=True):
    if entity_value:
        value = f'wd:{value_s}'
    else:
        value = f'"{value_s}"'
    return run_query(f'SELECT ?s WHERE {{ ?s wdt:{prop_s} {value} . }}')


def get_qualifiers(statement_s):
    return run_query(f'SELECT ?property ?value WHERE {{ '
                     f'VALUES ?proptypes {{owl:DatatypeProperty owl:ObjectProperty}} '
                     f'wds:{statement_s} ?property ?value. '
                     f'?property rdf:type ?proptypes }}')


def property_statements(entity_s, prop_s, full=True):
    res = run_query(f'SELECT ?s WHERE {{ wd:{entity_s} p:{prop_s} ?s . }}')
    if not full:
        return res
    d = {}
    for statement_s in res:
        d[statement_s] = get_qualifiers(statement_s)
    return d


def lookup_time(entity_s, prop_s):
    return run_query(f'SELECT ?value ?precision WHERE {{ '
                     f'wd:{entity_s} p:{prop_s} ?stmt . '
                     f'?stmt psv:P585 ?dataval . '
                     f'?dataval wikibase:timeValue ?value. '
                     f'?dataval wikibase:timePrecision ?precision. '
                     f'}}')
