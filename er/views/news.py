from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse

from er.models import NewsItem

@login_required
def index(request):
    """index page"""
    req_cxt = RequestContext(request)
    news_items = NewsItem.objects.all()

    context = Context({
	"doctitle" : "Melanoma RLC: News",
    	"news_items" : news_items,
        "tab" : "news",
    })

    return(render_to_response("news.html", context, context_instance=req_cxt))

