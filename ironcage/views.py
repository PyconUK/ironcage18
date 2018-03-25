import structlog

from django.shortcuts import redirect, render

logger = structlog.get_logger()


def index(request):
    return render(request, 'ironcage/index.html')


def error(request):
    1 / 0


def log(request):
    logger.info('Test log')
    return redirect('index')
