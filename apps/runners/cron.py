import requests
from django.conf import settings


def run_checks():
    ret = requests.post('{}/runners/run-checks'.format(settings.BASE_URL))
    print(ret.json())
    return ret.status_code


def cleanup_downtime():
    ret = requests.post('{}/runners/cleanup-downtime'.format(settings.BASE_URL))
    print(ret.json())
    return ret.status_code
