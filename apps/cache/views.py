from django.http import JsonResponse
from django.core.cache import cache


def reload_config_json(request):
    cache.clear()
    return JsonResponse({'status': 'OK'})