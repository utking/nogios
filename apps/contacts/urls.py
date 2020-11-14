"""nogios URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('api/users', views.users_json, name='users_json'),
    path('groups', views.groups, name='groups'),
    path('api/groups', views.groups_json, name='groups_json'),
    path('reload_config', views.reload_config, name='reload_config'),
    path('api/reload_config', views.reload_config_json, name='reload_config_json'),
    path('group/<str:name>', views.view_group, name='view_group'),
    path('api/group/<str:name>', views.view_group_json, name='view_group_json'),
    path('user/<str:name>', views.view_user, name='view_user'),
    path('api/user/<str:name>', views.view_user_json, name='view_user_json'),
]
