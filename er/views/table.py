from django.template import Context, RequestContext, Template
from django.template import loader as template_loader
from django.contrib.auth.decorators import login_required

from er.models import EvidenceReview, PaperTable
from er.models import Annotation, Comment

# table view interface

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse
from django.core.urlresolvers import reverse

from docutils import get_doc

from bs4 import BeautifulSoup

@login_required
def display_json(request, *args, **kwargs):
    """table modal view"""
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)
    this_url_name = request.resolver_match.url_name

    if doc == None:
        # TODO: fix this error handling once and for all
        raise ValueError

    tag_id = kwargs["block_id"]

    table = PaperTable.objects.get(tag_id=tag_id)

    docsoup = BeautifulSoup(doc.content, "html.parser")
    table_element = docsoup.find("table", id=tag_id)
    table_content = unicode(table_element)

    context = Context({
	"doc" : doc,
        "table" : table,
        "table_content" : table_content,
    })

    body_html = render_to_string("table_modal.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
    })

    return(HttpResponse(json, mimetype='application/json'))

