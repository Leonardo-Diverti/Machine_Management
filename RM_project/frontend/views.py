# Questo file gestisce le view del frontend e il rendering della dashboard.
from django.shortcuts import render


def index(request):
    """Serve la SPA frontend"""
    return render(request, 'frontend/index.html')
