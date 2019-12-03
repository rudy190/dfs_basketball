from datetime import (datetime, timedelta)

def get_datetime_begin_day():
    dateval = datetime.now()
    return dateval.replace(hour=0, minute=0, second=0, microsecond=0)

def date_range(start, end):
    day_interval = timedelta(days=1)
    while start < end:
        yield start.strftime('%m/%d/%Y')
        start += day_interval

def format_datetime_string(datetime_string):
    if datetime_string is not None:
        if ':' not in datetime_string:
            if '-' in datetime_string:
                value = datetime.strptime(datetime_string, '%Y-%m-%d')
            else:
                value = datetime.strptime(datetime_string, '%b %d, %Y')
        elif 'Z' in datetime_string:
            try:
                value = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
            except:
                try:
                    value = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S.000Z')
                except:
                    print(datetime_string)
        else:
            try:
                value = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S')
            except:
                print(datetime_string)
    return value
