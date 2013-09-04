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

from docutils import get_doc

import uuid

def atype_to_name(atype):
    for t in Annotation.ANNOTATION_TYPES:
        if t[0] == atype:
            return(t[1])

    return(None)

def annotation_summary(doc):
    counts = {
        "num_note" : 0,
        "num_openq" : 0,
        "num_proprev" : 0,
        "num_rev" : 0,
    }
    # the string-append is slow but probably insignificant
    for a in annotation.doc_all(doc):
        counts["num_" + a.atype] += 1

    return(counts)

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


    # TODO: should probably error out if annotation can't be found
    selected_annotation = 1

    if this_url_name in ["annotation_one_of_all", "annotation_one_in_block"]:
        requested_id = int(kwargs["annotation_id"])
    else:
        requested_id = None

    show_compose_button = False

    # get annotation type
    if this_url_name in ["annotation_all", "annotations_in_block"]:
        atype = kwargs["atype"]
    elif this_url_name in ["annotation_one_of_all", "annotation_one_in_block"]:
        # TODO: error checking?
        atype = annotation.fetch(kwargs["annotation_id"]).atype
    else:
        # should not be reached
        # TODO: raise proper exception (this will error out some other way)
        pass

    # get annotations
    if this_url_name in ["annotation_all", "annotation_one_of_all"]:
        # TODO: move this into annotation class
        annotations = [a for a in annotation.doc_all(doc) if a.atype == atype]
        if atype == "openq":
            show_compose_button = True
        reply_url_name = "annotation_reply"
    elif this_url_name in ["annotations_in_block", "annotation_one_in_block"]:
        # TODO: also use annotation class for this
        block = PaperBlock.objects.get(tag_id=kwargs["block_id"])
        objs = block.annotations.filter(atype=atype)
        annotations = [annotation.fetch(o.id) for o in objs]
        reply_url_name = "annotation_reply_in_block"
    else:
        # should not be reached
        # TODO: raise proper exception (this will error out some other way)
        pass

    num_annotations = len(annotations)
    for index, a in enumerate(annotations, 1):
        a.comments = a.comment.thread_as_list()
        a.reply_count = len(a.comments) - 1
        if requested_id != None:
            if a.model_object.id == requested_id:
                selected_annotation = index

    modal_id = "modal-{0}-{1}".format(doc.id, str(uuid.uuid4()))

    context = Context({
	"doc" : doc,
        "atype" : atype,
        "atype_name" : atype_to_name(atype),
	"modal_id" : modal_id,
	"annotations" : annotations,
	"num_annotations" : num_annotations,
        "this_url_name" : this_url_name,
        "selected_annotation" : selected_annotation,
        "show_compose_button" : show_compose_button,
        "reply_url_name" : reply_url_name,
    })
    
    if reply_url_name == "annotation_reply_in_block":
        context["block_id"] = kwargs["block_id"]

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

compose_choices = [c for c in Annotation.ANNOTATION_TYPES
                             if c[0] != 'rev']
# TODO: move this to model
default_choice="note"

class AnnotationComposeForm(forms.ModelForm):
    class Meta:
        model = Annotation
        # fields = ['atype'] 
        fields = [] 

    doc_id = forms.IntegerField(widget=forms.HiddenInput())
    atype = forms.ChoiceField(choices=compose_choices, widget=forms.RadioSelect, label = "Annotation Type")

    # initial_comment_text = forms.CharField(widget=CKEditorWidget(), label="")
    # following is for default text widget
    initial_comment_text = forms.CharField(widget=forms.Textarea(), label="")


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
        data["atype"] = default_choice
    elif this_url_name == 'annotation_compose':
        atype = kwargs["atype"]
        data["atype"] = atype
        block_id = None
        return_kwargs = dict(kwargs)
        del return_kwargs["atype"]
        form_action = reverse('annotation_new', kwargs=return_kwargs)
    else:
        # should not reach
        # TODO: raise correct extension
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
        "use_ckeditor" : True,
        "ckeditor_config" : "annotation_compose",
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
    user = request.user
    atype = form.cleaned_data["atype"]

    # TODO: reject this if atype == "rev"
    # (can't add revision directly like this, but perhaps editor can do
    # that later)

    init_comment = form.cleaned_data["initial_comment_text"]

    a = annotation(index="x", atype=atype, user=user, comment=init_comment)
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

class EditorProposedRevisionReplyForm(AnnotationReplyForm):
    APPROVAL_CHOICES = [
        ("accept", "Accept Revision"),
        ("reject", "Reject Revision"),
        ("defer", "Leave Under Consideration"),
    ]
    approval = forms.ChoiceField(choices=APPROVAL_CHOICES, widget=forms.RadioSelect, label = "")

@login_required
def reply_compose_json(request, *args, **kwargs):
    """annotation comment reply view"""
    this_url_name = request.resolver_match.url_name
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    # fetch original comment and its associated annotation
    # TODO: put this stuff into the comment/annotation class
    original_comment = comment.fetch(id=kwargs["comment_id"])
    root = original_comment.root
    a = annotation.fetch(id=root.model_object.annotation.id)

    atype = a.atype

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

    group_names = [g["name"] for g in request.user.groups.values()]

    if atype == "proprev" and "Editor" in group_names:
        data["approval"] = "defer"
        form = EditorProposedRevisionReplyForm(initial=data)
        form_type = "editor_reply"
    else:
        form = AnnotationReplyForm(initial=data)
        form_type = "normal_reply"

    if this_url_name == "annotation_reply":
        form_action = reverse('annotation_reply_new', kwargs=kwargs)
    elif this_url_name == "annotation_reply_in_block":
        form_action = reverse('annotation_reply_new_in_block', kwargs=kwargs)
    else:
        # should not be reached
        # TODO: raise error
        form_action = None

    context = Context({
	"doc" : doc,
	"modal_id" : modal_id,
        "form" : form,
        "form_action" : form_action,
        "form_type" : form_type,
        "original_comment" : original_comment,
    })

    body_html = render_to_string("reply_compose_inline.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
	"modal_id" : modal_id,
        "use_ckeditor" : True,
        "ckeditor_config" : "annotation_compose",
    })

    return(HttpResponse(json, mimetype='application/json'))

@login_required
@require_POST
def reply_add_json(request, *args, **kwargs):
    """annotation create"""

    this_url_name = request.resolver_match.url_name

    # fetch original comment and its associated annotation
    # TODO: put this stuff into the comment/annotation class
    original_comment = comment.fetch(id=kwargs["comment_id"])
    root = original_comment.root
    a = annotation.fetch(id=root.model_object.annotation.id)

    annotation_id = a.model_object.id

    atype = a.atype

    group_names = [g["name"] for g in request.user.groups.values()]

    if atype == "proprev" and "Editor" in group_names:
        form = EditorProposedRevisionReplyForm(request.POST)
        form_type = "editor_reply"
    else:
        form = AnnotationReplyForm(request.POST)
        form_type = "normal_reply"

    if form.is_valid():
        pass

    doc = get_doc(**kwargs)
    user = request.user
    new_comment_text = form.cleaned_data["comment_text"]

    new_comment = original_comment.reply(text=new_comment_text, user=user)

    change_modal = False
    if form_type == "editor_reply":
        approval = form.cleaned_data["approval"]
        if approval == "accept":
            # change to accepted revision
            a.atype = "rev"
            change_modal = True
            # TODO: record the change somewhere
        elif approval == "reject":
            # what do we do here?
            pass
        elif approval == "defer":
            # do nothing
            pass
        else:
            # TODO: raise something, probably
            pass

    return_kwargs = dict(kwargs, annotation_id=annotation_id)
    del return_kwargs["comment_id"]

    if this_url_name == "annotation_reply_new":
        return_url = reverse('annotation_one_of_all', kwargs=return_kwargs)
    elif this_url_name == "annotation_reply_new_in_block":
        return_url = reverse('annotation_one_in_block', kwargs=return_kwargs)
    else:
        # should not be reached
        # TODO: raise correct exception
        return_url = False

    context = Context({
        "comment" : new_comment,
    })

    new_comment_html = render_to_string("reply_comment.html", context)

    json_source = {
        "html" : new_comment_html,
        "change_modal" : change_modal,
    }

    if change_modal == True:
        json_source["url"] = return_url

    json = simplejson.dumps(json_source)

    return(HttpResponse(json, mimetype='application/json'))


@login_required
def preview_json(request, *args, **kwargs):
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    previews = []

    preview_template = template_loader.get_template("annotation_preview.html")

    # TODO: replace all of this with one big aggregation

    for block in doc.paperblock_set.all():
        block_id = block.tag_id
        context = {
            "doc" : doc,
            "block_id" : block_id,
        }

        preview_data = {
            "openq" : [],
            "note" : [],
            "proprev" : [],
            "rev" : [],
        }

        # TODO: make this use the annotation class
        # (for now, leave as-is because it can be very slow otherwise)
        for a in block.annotations.all():
            preview_data[a.atype].append(a)
        
        # get latest annotations

        for t in preview_data:
            context[t + "_list"] = preview_data[t]
            context[t + "_count"] = len(preview_data[t])

        # only look up the latest note date if there are any notes
        # (this is a workaround for performance; this should be worked into
        # the general aggregation stuff that needs to be done)
        if context["note_count"] > 0:
            from django.db.models import Max
            latest_date = block.annotations.filter(atype='note').aggregate(Max('initial_comment__timestamp'))
            context["note_date"] = latest_date["initial_comment__timestamp__max"]
            # context["note_date"] = None
        else:
            context["note_date"] = None

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

    summary_context = annotation_summary(doc)
    summary_html = render_to_string("annotation_summary.html", summary_context)

    return_data = {
        "status" : "ok",
        "previews" : previews,
        "summary_html" : summary_html,
    }
    json = simplejson.dumps(return_data)
    return(HttpResponse(json, mimetype='application/json'))

