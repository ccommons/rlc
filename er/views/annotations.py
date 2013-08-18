from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required

from er.models import EvidenceReview

# annotation view interface

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse
from er.annotation import annotation, comment
from django import forms

from document import get_doc

@login_required
def full_json(request, *args, **kwargs):
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
def compose_json(request, *args, **kwargs):
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

