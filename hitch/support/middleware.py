class RequestMiddleware(object):
    def process_request(self, request):
        chain = request.META.get('HTTP_X_FORWARDED_FOR')
        if chain:
            request.ip = chain.split(',')[0].strip()
        else:
            request.ip = request.META.get('REMOTE_ADDR')
            
        request.posting = (request.method == 'POST')
        request.scheme = ('https' if request.META.get('HTTPS') in ('on', '1') else 'http')