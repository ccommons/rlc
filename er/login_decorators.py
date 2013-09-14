from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

def login_required_json(f):
    def r(request, *args, **kwargs):
        if not request.user.is_authenticated():
            redirect_url = reverse('logged_out_json')
            return(HttpResponseRedirect(redirect_url))

        return(f(request, *args, **kwargs))

    return r

