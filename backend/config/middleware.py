"""Request-scoped helpers shared across the project."""
import threading

_thread_locals = threading.local()


def get_current_user():
    """Return the user attached to the request currently being handled, if any."""
    return getattr(_thread_locals, "user", None)


def get_current_request():
    return getattr(_thread_locals, "request", None)


class CurrentUserMiddleware:
    """
    Stashes the active request/user on thread-local storage so that model layers
    (audit columns on ``BaseModel``) can attribute writes without every caller
    threading the user through.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        _thread_locals.user = getattr(request, "user", None)
        try:
            return self.get_response(request)
        finally:
            _thread_locals.request = None
            _thread_locals.user = None
