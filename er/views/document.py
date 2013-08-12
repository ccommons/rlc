from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required

from er.models import EvidenceReview

@login_required
def index(request):
    """index page"""
    req_cxt = RequestContext(request)
    docs = EvidenceReview.objects.all()

    context = Context({
    	"docs" : docs,
    })

    return(render_to_response("index.html", context, context_instance=req_cxt))

def get_doc(**kwargs):
    if "er_id" in kwargs:
    	er_id = int(kwargs["er_id"])
    else:
    	er_id = -1

    try:
	doc = EvidenceReview.objects.get(id=er_id)
    except:
    	doc = None
	# XXX should redirect here to something sane

    return(doc)

@login_required
def fullpage(request, *args, **kwargs):
    """main page view"""
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    if doc != None:
    	content = doc.content
    else:
    	content = "no document"

    # print dir(request.user.groups)
    # print (request.user.groups.values())
    group_names = [g["name"] for g in request.user.groups.values()]
    # print [g.name for group in request.user.groups]

    sections = doc.papersections_set.order_by('position')

    context = Context({
	"doc" : doc,
    	"main_document" : content,
	"group_names" : group_names,
	"sections" : sections,
    })
    return(render_to_response("er.html", context, context_instance=req_cxt))

