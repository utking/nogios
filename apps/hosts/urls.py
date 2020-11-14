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
    path('api', views.hosts_json, name='hosts_json'),
    path('statuses', views.statuses, name='statuses'),
    path('api/statuses', views.statuses_json, name='statuses_json'),
    path('reload_config', views.reload_config, name='reload_config'),
    path('api/reload_config', views.reload_config_json, name='reload_config_json'),
    path('view/<str:name>', views.view, name='view'),
    path('api/view/<str:name>', views.view_json, name='view_json'),
    path('location/<str:name>', views.by_location, name='by_location'),
    path('api/location/<str:name>', views.by_location_json, name='by_location_json'),
]
