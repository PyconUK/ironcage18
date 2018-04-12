from django.http import HttpResponse


def http_trace_middleware(get_response):
    '''This middleware returns 405 (method not allowed) in reponse to an HTTP
    TRACE request.  This is required forr PCI DSS compliance.'''

    def middleware(request):
        if request.method == 'TRACE':
            return HttpResponse(status=405)

        return get_response(request)

    return middleware
