from datetime import datetime, timedelta
from json import loads
from calendar import Calendar


WEEK_DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

MONTH = [
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december'
    ]


def get_month_nth_weekday(year: int, month: int, week_day: int, nth: int):
    days = Calendar().itermonthdays2(year, month)
    index = 0
    result = []
    for day in days:
        if day[0] != 0 and day[1] + 1 == week_day:
            result.append(day[0])
            index = index + 1

    result.append(0)
    try:
        return result[nth - 1]
    except:
        pass
    return None


def get_months_days(year: int, start_month: int, start: int, end_month: int, end: int, every: int):
    result = []
    if start < 0:
        days = get_month_days(year=year, month=start_month, start=start, end=start, every=1)
        if len(days) > 0:
            start = days[0]
    if end < 0:
        days = get_month_days(year=year, month=end_month, start=end, end=end, every=1)
        if len(days) > 0:
            end = days[0]
    start_date = datetime.strptime('{}-{}-{}'.format(year, start_month, start), '%Y-%m-%d')
    end_date = datetime.strptime('{}-{}-{}'.format(year, end_month, end), '%Y-%m-%d')
    while start_date <= end_date:
        result.append((start_date.month, start_date.day))
        start_date = start_date + timedelta(days=1)

    try:
        return result[::every]
    except:
        pass
    return []


def get_month_days(year: int, month: int, start: int, end: int, every: int):
    days = Calendar().itermonthdays2(year, month)
    index = 0
    result = []
    for day in days:
        if day[0] != 0:
            result.append(day[0])
            index = index + 1
    try:
        if end < 0:
            end = len(result) + 1 + end
        if start < 0:
            start = len(result) + 1 + start
        return result[start - 1:end:every]
    except:
        pass
    return []


def is_in_time_range(needle: datetime.time, time_start: datetime.time, time_end: datetime.time):
    return time_start <= needle <= time_end


def is_in_times(needle: datetime.time, times: list):
    for time in times:
        start, end = time.split('-')
        time_start = datetime.strptime(start, '%H:%M')
        if end == '24:00':
            time_end = datetime.strptime('23:59:59', '%H:%M:%S')
        else:
            time_end = datetime.strptime(end, '%H:%M')
        if is_in_time_range(needle=needle, time_start=time_start.time(), time_end=time_end.time()):
            return True
    return False


def is_in_period(period: dict, date_time: datetime):
    date_in_period = False
    time_in_period = False
    dt = date_time.date()
    dates_str = period.get('dates')
    start_week_day = period.get('start_week_day')
    start_day = period.get('start_day')
    end_week_day = period.get('end_week_day')
    start_month = period.get('start_month')
    end_month = period.get('end_month')
    every = period.get('every')
    start_offset_str = period.get('start_offset')
    end_offset_str = period.get('end_offset')
    times_str = period.get('times')

    if every is None:
        every = 1
    else:
        every = int(every)

    if start_offset_str is None:
        start_offset = False
    else:
        start_offset = int(start_offset_str)

    if end_offset_str is None:
        end_offset = start_offset
    else:
        end_offset = int(end_offset_str)

    if start_month is None:
        start_month = False
    else:
        start_month = MONTH.index(start_month.lower()) + 1

    if end_month is None:
        end_month = start_month
    else:
        end_month = MONTH.index(end_month.lower()) + 1

    if dates_str is not None:
        date_in_period = __check_calendar_date(dates_str=dates_str, dt=dt, every=every)
    elif start_day is not None:
        end_day = period.get('end_day')
        if end_day is None:
            end_day = start_day

        date_in_period = __check_month_days(start=int(start_day), end=int(end_day), every=every,
                                            start_month=start_month, end_month=end_month, dt=date_time)
    elif start_week_day is not None:
        day_idx = date_time.weekday() + 1
        start_week_day_idx = WEEK_DAYS.index(start_week_day.lower())
        if end_week_day is not None:
            end_week_day_idx = WEEK_DAYS.index(end_week_day.lower())
        else:
            end_week_day_idx = start_week_day_idx
        if not start_offset and not end_offset:
            # example -- monday - thursday / 2
            date_in_period = __check_weekdays_no_offset(day=day_idx, every=every,
                                                        start=start_week_day_idx, end=end_week_day_idx)
        else:
            # for weekdays, default every must be 7 days (as in repeat every week)
            if end_offset == start_offset and end_week_day_idx == start_week_day_idx:
                every = period.get('every')
                if every is None:
                    every = 7
                else:
                    every = int(every)

            if not start_month and not end_month:
                # example -- monday 2 - wednesday 3 / 3
                date_in_period = __check_weekdays_with_offset_no_month(
                    start_off=start_offset, start=start_week_day_idx,
                    end_off=end_offset, end=end_week_day_idx, every=every, dt=date_time)
            else:
                # example -- monday 2 april - wednesday 3 may / 3
                date_in_period = __check_weekdays_with_offset_with_month(
                    start_off=start_offset,  start=start_week_day_idx,
                    end_off=end_offset, end=end_week_day_idx, every=every,
                    dt=date_time, start_month=start_month, end_month=end_month
                )

    if date_in_period:
        time_in_period = is_time_in_period(times_str=times_str, date_time=date_time)
    return date_in_period, time_in_period


def __check_month_days(start: int, end: int, every: int, start_month: int, end_month: int, dt: datetime):
    if start_month is None or not start_month:
        days = get_month_days(year=dt.year, month=dt.month, start=start, end=end, every=every)
        return dt.day in days
    else:
        days = get_months_days(year=dt.year,
                               start_month=start_month, start=start,
                               end_month=end_month, end=end,
                               every=every)
        return (dt.month, dt.day) in days


def __check_weekdays_no_offset(day: int, start: int, end: int, every: int):
    if end == start and end == day:
        return True
    elif day in range(start, end + 1, every) and min(start, end) <= day <= max(start, end):
        return True
    return False


def __check_weekdays_with_offset_with_month(start_off: int, start: int, end_off: int, end: int,
                                            every: int, dt: datetime, start_month: int, end_month: int):
    start_nth_week_day = get_month_nth_weekday(year=dt.year, month=dt.month,
                                               week_day=start, nth=start_off)
    end_nth_week_day = get_month_nth_weekday(year=dt.year, month=dt.month,
                                             week_day=end, nth=end_off)
    if start_month <= dt.month <= end_month:
        if start_nth_week_day is not None and end_nth_week_day is not None:
            start = datetime(year=dt.year, month=dt.month, day=start_nth_week_day)
            end = datetime(year=dt.year, month=dt.month, day=end_nth_week_day)
            if start.date() <= dt.date() <= end.date():
                diff_days = int((dt - start).total_seconds() / (3600 * 24))
                if diff_days % every == 0:
                    return True
    return False


def __check_weekdays_with_offset_no_month(start_off: int, start: int, end_off: int, end: int, every: int, dt: datetime):
    start_nth_week_day = get_month_nth_weekday(year=dt.year, month=dt.month,
                                               week_day=start, nth=start_off)
    end_nth_week_day = get_month_nth_weekday(year=dt.year, month=dt.month,
                                             week_day=end, nth=end_off)
    if start_nth_week_day is not None and end_nth_week_day is not None:
        start = datetime(year=dt.year, month=dt.month, day=start_nth_week_day)
        end = datetime(year=dt.year, month=dt.month, day=end_nth_week_day)
        if start.date() <= dt.date() <= end.date():
            diff_days = int((dt - start).total_seconds() / (3600 * 24))
            if diff_days % every == 0:
                return True
    return False


def __check_calendar_date(dates_str: str, dt: datetime.date, every: int):
    dates = dates_str.split(' - ')
    if len(dates) == 1:
        if every > 1:
            dt_item = datetime.strptime(dates[0], '%Y-%m-%d').date()
            diff_days = int((dt - dt_item).total_seconds() / (3600 * 24))
            if diff_days % every == 0:
                return True
        else:
            dt_item = datetime.strptime(dates[0], '%Y-%m-%d').date()
            if dt_item == dt:
                return True
    elif len(dates) == 2:
        dt_item_1 = datetime.strptime(dates[0], '%Y-%m-%d').date()
        dt_item_2 = datetime.strptime(dates[1], '%Y-%m-%d').date()
        if every > 1:
            diff_days = int((dt - dt_item_1).total_seconds() / (3600 * 24))
            return (dt_item_1 <= dt <= dt_item_2) and (diff_days % every == 0)
        else:
            return dt_item_1 <= dt <= dt_item_2
    return False


def is_time_in_period(times_str: str, date_time: datetime):
    if times_str is None or not isinstance(times_str, str):
        times = []
    else:
        times = times_str.split(',')
    for time_item in times:
        if is_in_times(needle=date_time.time(), times=time_item.split(',')):
            return True
    return False


def is_in_periods(periods: list, date_time: datetime = None):
    if date_time is None:
        date_time = datetime.now()
    if not isinstance(periods, list):
        raise Exception('No periods to check')
    for item in periods:
        is_date_in, is_time_in = is_in_period(period=item, date_time=date_time)
        if is_date_in and is_time_in:
            return True
    return False


if __name__ == '__main__':
    period_str = '{"parsed": []}'
    parsed = loads(period_str)['parsed']
    date = datetime.strptime('2020-11-13 20:59:59', '%Y-%m-%d %H:%M:%S')
    print(is_in_periods(periods=parsed, date_time=date))
