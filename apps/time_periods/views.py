from django.shortcuts import render, get_object_or_404, redirect
from apps.helpers.TimePeriodLoader import TimePeriodLoader
from apps.time_periods.models import TimePeriodConfig
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.conf import settings
from yaml import dump


def index(request):
    items = TimePeriodConfig.objects.order_by('name').all()
    return render(request, 'time_periods/index.html', {'items': items, 'title': 'Time periods'})


def time_periods_json(request):
    periods = TimePeriodConfig.objects.order_by('name').all()
    items = []
    for period in periods:
        items.append(model_to_dict(period))
    return JsonResponse({'items': items})


def view(request, item_id):
    item = get_object_or_404(klass=TimePeriodConfig, name=item_id)
    item_config = dump(item.config.get('periods'))
    return render(request, 'time_periods/view.html', {'item': item, 'config': item_config,
                                                      'title': 'Time period details'})


def view_json(request, item_id):
    item = get_object_or_404(klass=TimePeriodConfig, name=item_id)
    return JsonResponse({'item': model_to_dict(item)})


def reload_time_periods(save=True):
    base_path = settings.CONFIG_BASE_PATH / 'time_periods'
    loader = TimePeriodLoader(base_path=base_path)
    items = loader.load()

    if save:
        TimePeriodConfig.objects.all().delete()
        for item in items:
            TimePeriodConfig.objects.clear_cache(item['name'])
            TimePeriodConfig(name=item['name'], alias=item['alias'], config=item).save()
    return items


def reload_config(request):
    reload_config_json(request)
    return redirect(index)


def reload_config_json(request):
    reload_time_periods()
    return JsonResponse({'status': 'OK'})
