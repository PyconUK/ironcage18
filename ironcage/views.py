import structlog

from django.shortcuts import redirect

logger = structlog.get_logger()


def error(request):
    1 / 0


def log(request):
    logger.info('Test log')
    return redirect('index')
