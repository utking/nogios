from django.shortcuts import render, redirect
from django.core.cache import cache


def index(request):
    return redirect('/status')


def about(request):
    return render(request, 'home/about.html', {'title': 'About'})


def reset_cache(request):
    cache.clear()
    return redirect('/status')
