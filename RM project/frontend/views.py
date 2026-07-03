from django.shortcuts import render


def index(request):
    """Serve la SPA frontend"""
    return render(request, 'frontend/index.html')
