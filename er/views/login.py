from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.views.decorators.http import require_POST

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse

from er.models import NewsItem, Comment

from er.annotation import comment

from django import forms
from django.core.urlresolvers import reverse

import json

def logged_out_json(request):
    req_cxt = RequestContext(request)

    # currently, the javascript calls location.reload() to reload the page,
    # which will redirect to an appropriate login URL, with a (mostly)
    # correct redirect to the previous context
    # login_url = reverse('login')

    json_str = simplejson.dumps({
        "error" : "logged_out",
        # "login_url" : login_url,
    })

    return(HttpResponse(json_str, mimetype='application/json'))

