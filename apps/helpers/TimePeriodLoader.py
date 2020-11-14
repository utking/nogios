import re
from .config_loader import load_file
from .GenericLoader import GenericLoader


class TimePeriodLoader(GenericLoader):

    time_periods = []
    name_re = re.compile('^[0-9a-zA-Z_][a-zA-Z0-9_-]*[a-zA-Z0-9]+$')
    required_fields = [
        'name',
        'alias',
        'periods',
    ]
    MONTH = [
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december'
    ]
    WEEK_DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

    ACCEPTABLE_PERIOD_TEMPLATES = {
        'calendar_date':                 r'^\d\d\d\d-\d\d-\d\d\s+(.*)$',
        'specific_month_date':           r'^({})\s+[-]?\d+\s+(.*)$'.format('|'.join(MONTH)),
        'generic_month_date':            r'^day\s+\d+\s+(.*)$',
        'offset_weekday_specific_month': r'^\d+\s+({})\s+in\s+({})s+(.*)$'.format('|'.join(WEEK_DAYS), '|'.join(MONTH)),
        'offset_weekday':                r'^\d+\s+({})\s+(.*)$'.format('|'.join(WEEK_DAYS)),
        'normal_weekday':                r'^({})\s+(.*)$'.format('|'.join(WEEK_DAYS))
    }

    def __init__(self, base_path=None):
        super().__init__(base_path=base_path)

    @staticmethod
    def __parse_normal_weekday_period(line: str):
        tpl = re.compile(r'^(?:(?P<start_week_day>{})\s+'.format('|'.join(TimePeriodLoader.WEEK_DAYS)) +
                         r'(?:(?:(?P<start_offset>-?\d{1,3})(?:\s+(?P<start_month>%s))?)\s*)?' % (
                             '|'.join(TimePeriodLoader.MONTH)) +
                         r'(?:\s+-\s+(?P<end_week_day>{})\s+'.format('|'.join(TimePeriodLoader.WEEK_DAYS)) +
                         r'(?:(?:(?P<end_offset>-?\d{1,3})\s+(?P<end_month>%s)?)\s*)?)?)' % (
                             '|'.join(TimePeriodLoader.MONTH)) +
                         r'(?:\s*\/\s*(?P<every>\d{1,3}))?' +
                         r'\s*(?P<times>(?:\d{2}:\d{2}-\d{2}:\d{2})(?:,\d{2}:\d{2}-\d{2}:\d{2})*)\s*$')
        # print(tpl.pattern)
        parts = tpl.findall(line)
        if len(parts) != 1:
            raise Exception('Wrong format in [{}]'.format(line))
        return tpl.match(line).groupdict()

    @staticmethod
    def __parse_calendar_date_period(line: str):
        tpl = re.compile(r'^(?P<dates>\d{4}(?:-\d{2}){2}(?:\s-\s\d{4}(?:-\d{2}){2})?)' +
                         r'(?:\s\/\s(?P<every>\d{1,3}))?' +
                         r'\s+(?P<times>(?:\d{2}:\d{2}-\d{2}:\d{2})(?:,\d{2}:\d{2}-\d{2}:\d{2})*)\s*$')
        parts = tpl.findall(line)
        if len(parts) != 1:
            raise Exception('Wrong format in [{}]'.format(line))
        return tpl.match(line).groupdict()

    @staticmethod
    def __parse_generic_month_date_period(line: str):
        tpl = re.compile(r'^day\s+(?P<start_day>\d{1,2})' +
                         r'(?:\s+-\s+(?P<end_day>-?\d{1,3}))?' +
                         r'(?:\s\/\s(?P<every>\d{1,3}))?' +
                         r'\s+(?P<times>(?:\d{2}:\d{2}-\d{2}:\d{2})(?:,\d{2}:\d{2}-\d{2}:\d{2})*)\s*$')
        parts = tpl.findall(line)
        if len(parts) != 1:
            raise Exception('Wrong format in [{}]'.format(line))
        return tpl.match(line).groupdict()

    @staticmethod
    def __parse_specific_month_date_period(line: str):
        tpl = re.compile(r'^(?P<start_month>(%s))\s+(?P<start_day>-?\d{1,2})' % '|'.join(TimePeriodLoader.MONTH) +
                         r'(?:\s+-\s+(?:(?P<end_month>(%s))\s+)?(?P<end_day>\d{1,2}))?' % '|'.join(TimePeriodLoader.MONTH) +
                         r'(?:\s+\/\s+(?P<every>\d{1,2}))?' +
                         r'\s+(?P<times>(?:\d{2}:\d{2}-\d{2}:\d{2})(?:,\d{2}:\d{2}-\d{2}:\d{2})*)\s*$')
        parts = tpl.findall(line)
        if len(parts) != 1:
            raise Exception('Wrong format in [{}]'.format(line))
        return tpl.match(line).groupdict()

    def load(self):
        self.time_periods = []
        self.config_files.clear()
        item_names = []

        self.get_config_files()
        for full_path in self.config_files:
            cur_config = load_file(full_path)
            if cur_config is None:
                raise Exception('Time period Error in {}'.format(full_path))
            items = cur_config.get('time_periods')
            if items is None or not isinstance(items, list):
                raise Exception('{} - time_periods is not an array'.format(full_path))

            for item in items:
                self.check_required(item)
                if not self.name_re.match(item['name']):
                    raise Exception('Time period name {} must be of {}'.format(
                        item['name'], self.name_re.pattern))
                self.check_already_exists(item['name'], item_names)
                parsed_periods = self.__parse_periods(item['name'], item.get('periods'))
                item_names.append(item['name'])
                item['parsed'] = parsed_periods
                self.time_periods.append(item)

        print('Loading time_periods from {} Completed: {} time periods'.format(self.BASE_PATH, len(self.time_periods)))
        return self.time_periods

    def __parse_periods(self, name: str, periods: list):
        result = []
        if not isinstance(periods, list):
            raise Exception('Time periods items for {} are not a list'.format(name))
        for item in periods:
            matches = False
            for period_template in self.ACCEPTABLE_PERIOD_TEMPLATES:
                tpl = re.compile(self.ACCEPTABLE_PERIOD_TEMPLATES[period_template], flags=re.IGNORECASE)
                if tpl.match(item):
                    matches = True
                    if period_template == 'calendar_date':
                        result.append(self.__parse_calendar_date_period(item))
                    elif period_template == 'normal_weekday':
                        result.append(self.__parse_normal_weekday_period(item))
                    elif period_template == 'generic_month_date':
                        result.append(self.__parse_generic_month_date_period(item))
                    elif period_template == 'specific_month_date':
                        result.append(self.__parse_specific_month_date_period(item))
                    else:
                        raise Exception('[{}] Matches [{}]'.format(item, period_template))
                    break
            if not matches:
                raise Exception('[{}] Matches nothing'.format(item))
        return result
