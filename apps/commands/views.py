from django.shortcuts import render, get_object_or_404, redirect
from apps.helpers.CommandsLoader import CommandsLoader
from apps.commands.models import CommandConfig
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.conf import settings
from yaml import dump


def index(request):
    items = CommandConfig.objects.order_by('name').all()
    return render(request, 'commands/index.html', {'items': items, 'title': 'Commands'})


def commands_json(request):
    commands = CommandConfig.objects.order_by('name').all()
    items = []
    for command in commands:
        items.append(model_to_dict(command))
    return JsonResponse({'items': items})


def view(request, item_id):
    item = get_object_or_404(klass=CommandConfig, name=item_id)
    item_config = dump(item.config)
    return render(request, 'commands/view.html', {'item': item, 'config': item_config, 'title': 'Command details'})


def view_json(request, item_id):
    item = get_object_or_404(klass=CommandConfig, name=item_id)
    return JsonResponse({'item': model_to_dict(item)})


def reload_commands(save=True):
    base_path = settings.CONFIG_BASE_PATH / 'commands'
    loader = CommandsLoader(base_path=base_path)
    items = loader.load()

    if save:
        CommandConfig.objects.all().delete()
        for item in items:
            CommandConfig.objects.clear_cache(item['name'])
            CommandConfig(name=item['name'], alias=item['alias'], cmd=item['cmd'], config=item).save()
    return items


def reload_config(request):
    reload_config_json(request)
    return redirect(index)


def reload_config_json(request):
    reload_commands()
    return JsonResponse({'status': 'OK'})
