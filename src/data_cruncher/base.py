import click
import datetime
import pathlib
import requests
from dateutil.parser import parse as date_parse
import time
import yaml

WIKIDATA_REST_URL = 'https://www.wikidata.org/w/rest.php/wikibase/v1'
WIKIDATA_SPARQL_URL = 'https://query.wikidata.org/sparql'
UNKNOWN_TYPES = set()
CONFIG_PATH = pathlib.Path('config.yaml')

if CONFIG_PATH.exists():
    config = yaml.safe_load(open(CONFIG_PATH))
else:
    config = {}

DEFAULT_WAIT_TIME = config.get('default_wait_time', 1)
last_action_time = {}


def _stall(key):
    wait_time = config.get('wait_times', {}).get(key, DEFAULT_WAIT_TIME)
    now = datetime.datetime.now()

    if key in last_action_time:
        delta = now - last_action_time[key]
        delta_s = delta.total_seconds()

        time_to_wait = wait_time - delta_s
        if time_to_wait > 1e-9:
            if config.get('verbose', True):
                click.secho(f'Waiting {time_to_wait:.2f} seconds...')
            time.sleep(time_to_wait)

    last_action_time[key] = datetime.datetime.now()


def _get_rest_headers():
    headers = {}
    if 'user_agent' in config:
        headers['User-Agent'] = config['user_agent']
    if 'token' in config:
        headers['Authorization'] = 'Bearer ' + config['token']
    return headers


def get_rest(url, header_fields_to_copy=[], **params):
    full_url = WIKIDATA_REST_URL + url
    if 'format' not in params:
        params['format'] = 'json'

    _stall('get')

    resp = requests.get(
        full_url, params=params, headers=_get_rest_headers()
    )

    data = resp.json()
    for field in header_fields_to_copy:
        if field in resp.headers:
            data[field] = resp.headers[field]

    return data


def _get_message(content):
    if 'message' in content:
        return content['message']
    elif 'messageTranslations' in content:
        return content['messageTranslations']['en']
    else:
        return str(content)


def post_rest(url, body):
    full_url = WIKIDATA_REST_URL + url
    _stall('edit')
    resp = requests.post(
        full_url, json=body, headers=_get_rest_headers()
    )
    if resp.status_code != 201:
        msg = _get_message(resp.json())
        raise RuntimeError(f'{resp.status_code} {msg}')
    return resp.json()


def patch_rest(url, body):
    full_url = WIKIDATA_REST_URL + url
    _stall('edit')
    resp = requests.patch(
        full_url, json=body, headers=_get_rest_headers()
    )
    if resp.status_code != 200:
        msg = _get_message(resp.json())
        raise RuntimeError(f'{resp.status_code} {msg}')
    return resp.json()


def _get_sparql_headers():
    headers = {}
    if 'user_agent' in config:
        headers['User-Agent'] = config['user_agent']
    return headers


def sparql_query(qs):
    """Run a sparql query on wikidata and return the structured results"""

    params = {'query': qs, 'format': 'json'}
    _stall('sparql')
    req = requests.get(WIKIDATA_SPARQL_URL, params=params, headers=_get_sparql_headers())
    if req.status_code != 200:
        raise RuntimeError(f'{req.status_code} {req.content}')
    return req.json()


def parse_sparql_results(results):
    parsed = []
    for result in results['results']['bindings']:
        d = []
        for key, value_d in result.items():
            vtype = value_d['type']
            if vtype == 'uri':
                v = value_d['value']
                v = v.replace('http://www.wikidata.org/entity/statement/', '')
                v = v.replace('http://www.wikidata.org/entity/', '')
                v = v.replace('http://www.wikidata.org/prop/qualifier/', '')
                v = v.replace('http://www.wikidata.org/prop/statement/', '')
                d.append((key, v))
            elif vtype == 'literal':
                if 'datatype' in value_d:
                    dt = value_d['datatype']
                    if dt == 'http://www.w3.org/2001/XMLSchema#dateTime':
                        v = date_parse(value_d['value'])
                    elif dt == 'http://www.w3.org/2001/XMLSchema#integer':
                        v = int(value_d['value'])
                    else:
                        click.secho(f'Unknown datatype: {repr(dt)}', fg='yellow')
                        v = value_d['value']
                else:
                    v = value_d['value']
                d.append((key, v))
            else:
                if vtype not in UNKNOWN_TYPES:
                    UNKNOWN_TYPES.add(vtype)
                    click.secho(f'Unknown result type: {repr(vtype)}', fg='yellow')
                continue
        if len(d) == 1:
            parsed.append(d[0][1])
        else:
            parsed.append(dict(d))
    return parsed


def run_query(qs):
    return parse_sparql_results(sparql_query(qs))
