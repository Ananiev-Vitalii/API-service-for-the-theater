from functools import wraps
from django.http import Http404


def ajax_only(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            raise Http404()
        return view_func(request, *args, **kwargs)

    return _wrapped
