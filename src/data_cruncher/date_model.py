from enum import IntEnum
from dateutil.parser import parse as date_parse


class Precision(IntEnum):
    BILLION_YEARS = 0
    HUNDRED_MILLION_YEARS = 1
    TEN_MILLION_YEARS = 2
    MILLION_YEARS = 3
    HUNDRED_THOUSAND_YEARS = 4
    TEN_THOUSAND_YEARS = 5
    MILLENNIUM = 6
    CENTURY = 7
    DECADE = 8
    YEAR = 9
    MONTH = 10
    DAY = 11
    HOUR = 12
    MINUTE = 13
    SECOND = 14


class WikiDate(dict):
    def __init__(self, dt, precision):
        self['calendarmodel'] = 'http://www.wikidata.org/entity/Q1985727'
        self.precision = precision
        self['precision'] = precision.value

        if isinstance(dt, str):
            dt = date_parse(dt)

        self.dt = dt.replace(microsecond=0)
        self['time'] = dt.strftime('+%Y-%m-%dT%H:%M:%SZ')
