from django.template import Context, RequestContext, Template
from django.template import loader as template_loader
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from er.models import EvidenceReview, PaperBlock
from er.models import Annotation, Comment

from er.annotation import annotation, comment

# annotation view interface

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse
from django import forms
from django.core.urlresolvers import reverse

from ckeditor.widgets import CKEditorWidget

from document import get_doc

def atype_to_name(atype):
    for t in Annotation.ANNOTATION_TYPES:
        if t[0] == atype:
            return(t[1])

    return(None)


@login_required
def full_json(request, *args, **kwargs):
    """annotation view"""
    req_cxt = RequestContext(request)

    this_url_name = request.resolver_match.url_name

    doc = get_doc(**kwargs)

    if doc != None:
    	content = doc.content
    else:
        content = "no document"

    atype = kwargs["atype"]

    # TODO: should probably error out if annotation can't be found
    selected_annotation = 1

    if this_url_name in ["annotation_one_of_all", "annotation_one_in_block"]:
        requested_id = int(kwargs["annotation_id"])
    else:
        requested_id = None

    show_compose_button = False

    # get annotations
    if this_url_name in [ "annotation", "annotation_one_of_all" ]:
        # TODO: move this into annotation class
        annotations = [a for a in annotation.doc_all(doc) if a.atype == atype]
        if atype == "openq":
            show_compose_button = True
    else:
        # TODO: also use annotation class for this
        block = PaperBlock.objects.get(tag_id=kwargs["block_id"])
        objs = block.annotations.filter(atype=atype)
        annotations = [annotation.fetch(o.id) for o in objs]

    num_annotations = len(annotations)
    for index, a in enumerate(annotations, 1):
        a.comments = a.comment.thread_as_list()
        a.reply_count = len(a.comments) - 1
        if requested_id != None:
            if a.model_object.id == requested_id:
                selected_annotation = index

    modal_id = "modal-{0}".format(doc.id)

    context = Context({
	"doc" : doc,
        "atype" : kwargs["atype"],
        "atype_name" : atype_to_name(kwargs["atype"]),
	"modal_id" : modal_id,
	"annotations" : annotations,
	"num_annotations" : num_annotations,
        "this_url_name" : this_url_name,
        "selected_annotation" : selected_annotation,
        "show_compose_button" : show_compose_button,
    })

    if (this_url_name == "annotation" and atype == "openq"):
        compose_kwargs = {
            "doc_id" : kwargs["doc_id"],
            "atype" : kwargs["atype"],
        }
        context["compose_url"] = reverse('annotation_compose', kwargs=compose_kwargs)

    body_html = render_to_string("annotation.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
	"modal_id" : modal_id,
    })

    return(HttpResponse(json, mimetype='application/json'))

class AnnotationComposeForm(forms.ModelForm):
    class Meta:
        model = Annotation
        fields = ['atype'] 

    doc_id = forms.IntegerField(widget=forms.HiddenInput())

    # initial_comment_text = forms.CharField(widget=CKEditorWidget())
    # following is for default text widget
    initial_comment_text = forms.CharField(widget=forms.Textarea())

@login_required
def compose_json(request, *args, **kwargs):
    """annotation compose view"""
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)
    this_url_name = request.resolver_match.url_name

    if doc == None:
        # TODO: fix this error handling once and for all
        raise ValueError

    data = {
        "doc_id" : doc.id,
        "initial_comment_text" : "",
    }

    if this_url_name == 'annotation_compose_in_block':
        block_id = kwargs["block_id"]
        form_action = reverse('annotation_new_in_block', kwargs=kwargs)
    elif this_url_name == 'annotation_compose':
        atype = kwargs["atype"]
        data["atype"] = atype
        block_id = None
        form_action = reverse('annotation_new', kwargs=kwargs)
    else:
        # should not reach
        block_id = None


    modal_id = "modal-compose-{0}".format(doc.id)

    form = AnnotationComposeForm(initial=data)

    # if there is no block, this is an open question and we do not allow
    # the user to choose the annotation type
    if block_id == None:
        form.fields["atype"].widget = forms.HiddenInput()

    context = Context({
	"doc" : doc,
        # "atype_name" : atype_to_name(kwargs["atype"]),
	"modal_id" : modal_id,
        "form" : form,
        "form_action" : form_action,
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
    this_url_name = request.resolver_match.url_name

    form = AnnotationComposeForm(request.POST)

    if form.is_valid():
        pass

    doc = get_doc(**kwargs)
    username = request.user.username
    atype = form.cleaned_data["atype"]
    init_comment = form.cleaned_data["initial_comment_text"]

    a = annotation(index="x", atype=atype, user=username, comment=init_comment)
    a.document = doc

    if this_url_name == "annotation_new_in_block":
        # TODO: move this to model
        block = PaperBlock.objects.get(tag_id=kwargs["block_id"])
        a.model_object.doc_block = block
        a.model_object.save()

    return_kwargs = dict(kwargs, annotation_id=a.model_object.id)

    if this_url_name == "annotation_new":
        return_url = reverse('annotation_one_of_all', kwargs=return_kwargs)
    elif this_url_name == "annotation_new_in_block":
        return_kwargs["atype"] = atype
        return_url = reverse('annotation_one_in_block', kwargs=return_kwargs)
    else:
        # should not be reached
        return_url = None

    json = simplejson.dumps({
    	"annotation_id" : a.model_object.id,
        "url" : return_url,
    })

    # TODO: fill in the rest of this
    return(HttpResponse(json, mimetype='application/json'))


class AnnotationReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [] 

    # comment_text = forms.CharField(widget=CKEditorWidget())
    # following is for default text widget
    comment_text = forms.CharField(widget=forms.Textarea())

@login_required
def reply_json(request, *args, **kwargs):
    """annotation comment reply view"""
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    if doc == None:
        # TODO: fix this error handling once and for all
        raise ValueError

    # section = None
    
    # TODO: validate comment ID

    original_comment = comment.fetch(id=kwargs["comment_id"])

    data = {
        "comment_text" : "",
    }

    modal_id = "modal-reply-{0}".format(kwargs["comment_id"])

    form = AnnotationReplyForm(initial=data)

    form_action = reverse('annotation_reply_new', kwargs=kwargs)
    print form_action

    context = Context({
	"doc" : doc,
	"modal_id" : modal_id,
        "form" : form,
        "form_action" : form_action,
        "original_comment" : original_comment,
    })

    body_html = render_to_string("annotation_reply.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
	"modal_id" : modal_id,
    })

    return(HttpResponse(json, mimetype='application/json'))

@login_required
@require_POST
def reply_add_json(request, *args, **kwargs):
    """annotation create"""

    form = AnnotationReplyForm(request.POST)

    if form.is_valid():
        pass

    doc = get_doc(**kwargs)
    username = request.user.username
    new_comment_text = form.cleaned_data["comment_text"]

    original_comment_id = kwargs["comment_id"]
    original_comment = comment.fetch(id=original_comment_id)

    new_comment = original_comment.reply(text=new_comment_text, user=username)

    return_kwargs = dict(kwargs)
    del return_kwargs["comment_id"]
    return_url = reverse('annotation_one_of_all', kwargs=return_kwargs)

    json = simplejson.dumps({
    	"annotation_id" : kwargs["annotation_id"],
        "url" : return_url,
    })

    # TODO: fill in the rest of this
    return(HttpResponse(json, mimetype='application/json'))


@login_required
def preview_json(request, *args, **kwargs):
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    previews = []

    preview_template = template_loader.get_template("annotation_preview.html")

    for block in doc.paperblock_set.all():
        block_id = block.tag_id
        context = {
            "doc" : doc,
            "block_id" : block_id,
        }

        # XXX pull these from model
        preview_data = {
            "openq" : [],
            "note" : [],
            "proprev" : [],
            "rev" : [],
        }

        # TODO: make this use the annotation class
        for a in block.annotations.all():
            preview_data[a.atype].append(a)
        
        for t in preview_data:
            context[t + "_list"] = preview_data[t]
            context[t + "_count"] = len(preview_data[t])

        context["compose_url"] = reverse("annotation_compose_in_block", kwargs={
            "doc_id" : kwargs["doc_id"],
            "block_id" : block_id,
        })

        html = preview_template.render(Context(context))
        # html = render_to_string("annotation_preview.html", context, context_instance=req_cxt)
        previews.append({
            "block_id" : block_id,
            "html" : html,
        })

    json = simplejson.dumps(previews)
    return(HttpResponse(json, mimetype='application/json'))

