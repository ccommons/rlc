from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from django.views.decorators.cache import patch_cache_control
from django.utils.cache import add_never_cache_headers

def login_required_json(f):
    def r(request, *args, **kwargs):
        if not request.user.is_authenticated():
            redirect_url = reverse('logged_out_json')
            response = HttpResponseRedirect(redirect_url)
        else:
            response = f(request, *args, **kwargs)

        patch_cache_control(response, private=True, no_cache=True, no_store=True, must_revalidate=True)
        add_never_cache_headers(response)
        return(response)

    return r

