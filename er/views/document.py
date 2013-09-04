from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required

from er.models import EvidenceReview

from django.core.urlresolvers import reverse

from copy import deepcopy

from docutils import get_doc
from annotations import annotation_summary

@login_required
def index(request):
    """index page"""
    req_cxt = RequestContext(request)
    docs = EvidenceReview.objects.all()

    context = Context({
	"doctitle" : "Melanoma RLC: home",
    	"docs" : docs,
        "tab" : "documents",
    })

    return(render_to_response("index.html", context, context_instance=req_cxt))

@login_required
def fullpage(request, *args, **kwargs):
    """main page view"""
    from er.notification import notification
    notification.mark_read(request)
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    if doc != None:
    	content = doc.content
    else:
    	content = "no document"

    group_names = [g["name"] for g in request.user.groups.values()]

    sections = doc.papersection_set.order_by('position')

    summary = annotation_summary(doc)

    # get URL reverse kwargs for viewing open questions
    oq_kwargs = deepcopy(kwargs)
    oq_kwargs["atype"] = "openq"
    # openq_url = reverse('annotation', kwargs=oq_kwargs)

    # TODO: fix this
    from annotations import AnnotationComposeForm
    dummyform = AnnotationComposeForm()
    widget_media = dummyform.media

    # TODO: formalize this
    override_ckeditor = True

    context = {
	"doc" : doc,
	"doctitle" : "Melanoma RLC: " + doc.title,
    	"main_document" : content,
        "widget_media" : widget_media,
        "override_ckeditor" : override_ckeditor,
	"group_names" : group_names,
	"sections" : sections,
        # "openq_url" : openq_url,
        "tab" : "documents",
    }
    context.update(summary)

    return(render_to_response("er.html", context, context_instance=req_cxt))

