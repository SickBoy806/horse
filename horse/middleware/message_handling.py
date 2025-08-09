from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ValidationError

class MessageErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect(request.path)
