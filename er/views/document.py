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
	"doctitle" : "Melanoma RLC: home",
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

    group_names = [g["name"] for g in request.user.groups.values()]

    sections = doc.papersection_set.order_by('position')

    context = Context({
	"doc" : doc,
	"doctitle" : "Melanoma RLC: " + doc.title,
    	"main_document" : content,
	"group_names" : group_names,
	"sections" : sections,
    })
    return(render_to_response("er.html", context, context_instance=req_cxt))


# annotation view interface

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse
from er.annotation import annotation, comment
from django import forms

@login_required
def annotation_json(request, *args, **kwargs):
    """annotation view"""
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    if doc != None:
    	content = doc.content
    else:
        content = "no document"

    atype = kwargs["atype"]

    annotations = doc.annotations.all()
    num_annotations = len(annotations)
    if num_annotations == 0:
	a = None
	comments = []
    else:
	a = annotation.fetch(annotations[0].id)
	comments = a.comment.thread_as_list()
	author = a.comment.user

    modal_id = "modal-{0}".format(doc.id)
    context = Context({
	"doc" : doc,
	"modal_id" : modal_id,
	"comments" : comments,
	"reply_count" : len(comments) - 1,
	"num_annotations" : num_annotations,
    })

    body_html = render_to_string("annotation.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
	"modal_id" : modal_id,
	"test" : 1,
    })

    return(HttpResponse(json, mimetype='application/json'))

class AnnotationComposeForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())
    atype = forms.CharField(max_length=100)
    text = forms.CharField(widget=forms.Textarea())
    # content = forms.CharField(widget=CKEditorWidget())
    # following is for default text widget
    # content = forms.CharField(widget=forms.Textarea())

@login_required
def annotation_compose_json(request, *args, **kwargs):
    """main compose view"""
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    if doc != None:
    	content = doc.content
    else:
        content = "no document"

    atype = kwargs["atype"]

    modal_id = "modal-compose-{0}".format(doc.id)

    context = Context({
	"doc" : doc,
	"modal_id" : modal_id,
    })

    body_html = render_to_string("annotation_compose.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
	"modal_id" : modal_id,
    })

    return(HttpResponse(json, mimetype='application/json'))

