from django.shortcuts import render, get_object_or_404, redirect
from apps.helpers.ContactsLoader import ContactsLoader
from apps.contacts.models import GroupContactConfig, UserContactConfig
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.conf import settings


def index(request):
    items = UserContactConfig.objects.get_all()
    return render(request, 'contacts/index.html', {'items': items, 'title': 'User contacts'})


def users_json(request):
    users = UserContactConfig.objects.get_all()
    items = []
    for user in users:
        items.append(model_to_dict(user))
    return JsonResponse({'items': items})


def groups(request):
    items = GroupContactConfig.objects.get_all()
    return render(request, 'contacts/groups.html', {'items': items, 'title': 'Groups'})


def groups_json(request):
    groups = GroupContactConfig.objects.get_all()
    items = []
    for group in groups:
        items.append(model_to_dict(group))
    return JsonResponse({'items': items})


def view_user(request, name):
    item = get_object_or_404(klass=UserContactConfig, name=name)
    return render(request, 'contacts/view_user.html', {'item': item, 'title': 'User details'})


def view_user_json(request, name):
    item = get_object_or_404(klass=UserContactConfig, name=name)
    return JsonResponse({'item': model_to_dict(item)})


def view_group(request, name):
    item = get_object_or_404(klass=GroupContactConfig, name=name)
    return render(request, 'contacts/view_group.html', {'item': item, 'title': 'Group details'})


def view_group_json(request, name):
    item = get_object_or_404(klass=GroupContactConfig, name=name)
    return JsonResponse({'item': model_to_dict(item)})


def reload_contacts(save=True):
    base_path = settings.CONFIG_BASE_PATH / 'contacts'
    loader = ContactsLoader(base_path=base_path)
    contact_users, contact_groups = loader.load()

    if save:
        UserContactConfig.objects.all().delete()
        for item in contact_users:
            UserContactConfig(name=item['name'], config=item,
                              channel=item['channel'], destination=item['destination'],
                              ).save()

    if save:
        GroupContactConfig.objects.all().delete()
        for item in contact_groups:
            GroupContactConfig(name=item['name'], config=item).save()

    return contact_users, contact_groups


def reload_config(request):
    reload_config_json(request)
    return redirect(index)


def reload_config_json(request):
    reload_contacts()
    return JsonResponse({'status': 'OK'})


def load_contacts():
    contacts_base_path = settings.CONFIG_BASE_PATH / 'contacts'
    contacts_loader = ContactsLoader(base_path=contacts_base_path)
    return contacts_loader.load()
