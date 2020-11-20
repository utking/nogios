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
    path('', views.services, name='services'),
    path('hosts', views.hosts, name='hosts'),
    path('api/hosts', views.hosts_json, name='hosts_json'),
    path('api/services', views.services_json, name='services_json'),
    path('services', views.services, name='services'),
    path('unhandled', views.unhandled, name='unhandled'),
    path('api/unhandled', views.unhandled_json, name='unhandled_json'),
    path('host-services/<str:host_name>', views.host_services, name='host-services'),
    path('api/host-services/<str:host_name>', views.host_services_json, name='host_services_json'),
    path('service/<str:host_name>/<str:service_name>', views.service, name='service'),
    path('api/service/<str:host_name>/<str:service_name>', views.service_json, name='service_json'),
    path('service/down', views.service_down, name='service_down'),
    path('api/service/down', views.service_down_json, name='service_down_json'),
    path('service/ack', views.service_ack, name='service_ack'),
    path('api/service/ack', views.service_ack_json, name='service_ack_json'),
    path('host/down', views.host_down, name='host_down'),
    path('host/ack', views.host_ack, name='host_ack'),
    path('api/host/ack', views.host_ack_json, name='host_ack_json'),
    path('host/<str:host_name>', views.host, name='host'),
    path('api/host/<str:host_name>', views.host_json, name='host_json'),
]
