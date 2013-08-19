from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


from er.models import EvidenceReview
from er.models import Annotation

# annotation view interface

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse
from er.annotation import annotation, comment
from django import forms
from django.core.urlresolvers import reverse

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

    # TODO: move this into annotation class
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
        "compose_url" : reverse('annotation_compose', kwargs=kwargs),
    })

    body_html = render_to_string("annotation.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
	"modal_id" : modal_id,
	"test" : 1,
    })

    return(HttpResponse(json, mimetype='application/json'))

class AnnotationComposeForm(forms.ModelForm):
    class Meta:
        model = Annotation
        fields = ['atype'] 

    doc_id = forms.IntegerField(widget=forms.HiddenInput())

    initial_comment_text = forms.CharField(widget=forms.Textarea())
    # initial_comment_text = forms.CharField(widget=CKEditorWidget())
    # following is for default text widget

@login_required
def compose_json(request, *args, **kwargs):
    """annotation compose view"""
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    if doc == None:
        # TODO: fix this error handling once and for all
        raise ValueError

    atype = kwargs["atype"]

    section = None

    data = {
        "doc_id" : doc.id,
        "atype" : atype,
        "initial_comment_text" : "bubb rubb",
    }

    modal_id = "modal-compose-{0}".format(doc.id)

    form = AnnotationComposeForm(data)

    # if there is no section, this is an open question and we do not allow
    # the user to choose the annotation type
    if section == None:
        form.fields["atype"].widget = forms.HiddenInput()

    context = Context({
	"doc" : doc,
	"modal_id" : modal_id,
        "form" : form,
        # TODO: fix fixed URL
        "form_action" : reverse('annotation_new', kwargs=kwargs),
    })

    body_html = render_to_string("annotation_compose.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
	"modal_id" : modal_id,
    })

    return(HttpResponse(json, mimetype='application/json'))

@login_required
@require_POST
def add_json(request, *args, **kwargs):
    """annotation create"""
    req_cxt = RequestContext(request)

    form = AnnotationComposeForm(request.POST)

    if form.is_valid():
        pass

    doc = get_doc(**kwargs)
    username = request.user.username
    atype = form.cleaned_data["atype"]
    comment = form.cleaned_data["initial_comment_text"]

    a = annotation(index="x", atype=atype, user=username, comment=comment)
    # TODO: move this into annotation class
    a.model_object.er_doc = doc
    a.model_object.save()

    json = simplejson.dumps({
    	"annotation_id" : a.model_object.id,
        "url" : reverse('annotation', kwargs=kwargs),
    })

    # TODO: fill in the rest of this
    return(HttpResponse(json, mimetype='application/json'))


