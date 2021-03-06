from django.template import Context, RequestContext, Template
from django.template import loader as template_loader
from django.contrib.auth.decorators import login_required
from er.login_decorators import login_required_json
from django.views.decorators.http import require_POST
from django.db.models import Count, Max

from er.models import EvidenceReview, PaperBlock, PaperTable
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

from ratings import attach_ratings
from follow import attach_following

def atype_to_name(atype):
    for t in Annotation.ANNOTATION_TYPES:
        if t[0] == atype:
            return(t[1])

    return(None)

def annotation_summary(doc):
    counts = { "num_"+atype: 0 for atype, text in Annotation.ANNOTATION_TYPES }

    # TODO: this can be an aggregation, but the performance of this is
    # currently not an issue

    for a in annotation.doc_all(doc):
        counts["num_"+a.atype] += 1

    return(counts)

def open_questions_for_main_doc(doc):
    open_questions = Annotation.objects.select_related('doc_block','initial_comment','initial_comment__user').filter(er_doc=doc.id, atype='openq').order_by('doc_block__position', 'timestamp')
    return(open_questions)

@login_required_json
def full_json(request, *args, **kwargs):
    """annotation view"""
    from er.notification import notification
    notification.mark_read(request)
    req_cxt = RequestContext(request)

    user = request.user

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

    # TODO: put context info into class method in annotation class
    # (see later)

    annotation_objs = Annotation.objects.filter(id__in=[a.id for a in annotations])
    # get context info
    context_info = annotation_objs.exclude(doc_block=None).values_list('id', 'doc_block__tag_id', 'doc_block__preview_text')
    block_context = { id: { "tag_id": tag_id, "context": context }
                                for id, tag_id, context in context_info }

    # get tables and caption info
    table_info = doc.papertable_set.values_list('tag_id', 'caption')
    table_captions = { tag_id: caption for tag_id, caption in table_info }


    num_annotations = len(annotations)
    for index, a in enumerate(annotations, 1):
        a.comments = a.comment.thread_as_list()
        attach_ratings(a.comments, user=user)
        attach_following(a.comments, user)
        a.reply_count = len(a.comments) - 1
        if requested_id != None:
            if a.model_object.id == requested_id:
                selected_annotation = index

        # extract and connect context if necessary
        # TODO: context-attaching to a set of annotations should probably be
        # a class method in the annotation class
        if a.id in block_context:
            a.show_context = True
            a.tag_id = block_context[a.id]["tag_id"]
            if a.tag_id in table_captions:
                a.context = table_captions[a.tag_id]
            else:
                a.context = block_context[a.id]["context"]
        else:
            a.show_context = False

    context = Context({
	"doc" : doc,
        "atype" : atype,
        "atype_name" : atype_to_name(atype),
	"annotations" : annotations,
	"num_annotations" : num_annotations,
        "this_url_name" : this_url_name,
        "selected_annotation" : selected_annotation,
        "show_compose_button" : show_compose_button,
        "reply_url_name" : reply_url_name,
        "user" : user,
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
    })

    return(HttpResponse(json, mimetype='application/json'))

compose_choices = Annotation.compose_choices
default_choice = Annotation.default_choice

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


@login_required_json
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


    form = AnnotationComposeForm(initial=data)

    # if there is no block, this is an open question and we do not allow
    # the user to choose the annotation type
    if block_id == None:
        form.fields["atype"].widget = forms.HiddenInput()

    context = Context({
	"doc" : doc,
        "this_url_name" : this_url_name,
        # "atype_name" : atype_to_name(kwargs["atype"]),
        "form" : form,
        "form_action" : form_action,
    })

    body_html = render_to_string("annotation_compose.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
        "use_ckeditor" : True,
        "ckeditor_config" : "annotation_compose",
    })

    return(HttpResponse(json, mimetype='application/json'))

@login_required_json
@require_POST
def add_json(request, *args, **kwargs):
    """annotation create"""

    req_cxt = RequestContext(request)
    this_url_name = request.resolver_match.url_name
    doc = get_doc(**kwargs)

    form = AnnotationComposeForm(request.POST)

    if not form.is_valid():
        # return form with indicated errors

        if this_url_name == "annotation_new_in_block":
            # return_kwargs = dict(kwargs)
            form_action = reverse('annotation_new_in_block', kwargs=kwargs)
        else:    # this_url_name == "annotation_new":
            # if there's no block ID, this is an open question;
            # field type must be hidden
            form.fields["atype"].widget = forms.HiddenInput()
            form_action = reverse('annotation_new', kwargs=kwargs)

        context = Context({
            "doc" : doc,
            "form" : form,
            "form_action" : form_action,
        })

        body_html = render_to_string("annotation_compose.html", context, context_instance=req_cxt)
        json = simplejson.dumps({
            "error" : "invalid form data",
            "body_html" : body_html,
            "use_ckeditor" : True,
            "ckeditor_config" : "annotation_compose",
        })

        return(HttpResponse(json, mimetype='application/json'))

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

    from er.eventhandler import commentAnnotationEventHandler as caeh
    caeh.notify(a.comment.model_object, action='new')

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

@login_required_json
def reply_compose_json(request, *args, **kwargs):
    """annotation comment reply view"""
    this_url_name = request.resolver_match.url_name
    req_cxt = RequestContext(request)

    user = request.user

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

    group_names = [g["name"] for g in request.user.groups.values()]

    if atype == "proprev" and "Editor" in group_names and user != original_comment.user:
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
        "form" : form,
        "form_action" : form_action,
        "form_type" : form_type,
        "original_comment" : original_comment,
    })

    body_html = render_to_string("reply_compose_inline.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
        "use_ckeditor" : True,
        "ckeditor_config" : "annotation_compose",
    })

    return(HttpResponse(json, mimetype='application/json'))

@login_required_json
@require_POST
def reply_add_json(request, *args, **kwargs):
    """annotation create"""

    this_url_name = request.resolver_match.url_name
    user = request.user

    # fetch original comment and its associated annotation
    # TODO: put this stuff into the comment/annotation class
    original_comment = comment.fetch(id=kwargs["comment_id"])
    root = original_comment.root
    a = annotation.fetch(id=root.model_object.annotation.id)

    doc = get_doc(**kwargs)

    annotation_id = a.model_object.id

    atype = a.atype

    group_names = [g["name"] for g in request.user.groups.values()]

    if atype == "proprev" and "Editor" in group_names and user != original_comment.user:
        form = EditorProposedRevisionReplyForm(request.POST)
        form_type = "editor_reply"
    else:
        form = AnnotationReplyForm(request.POST)
        form_type = "normal_reply"

    if not form.is_valid():
        # render form with errors (possibly merge with earlier form)
        context = Context({
            "doc" : doc,
            "form" : form,
            "form_action" : request.path,
            "form_type" : form_type,
            "original_comment" : original_comment,
        })

        req_cxt = RequestContext(request)
        resubmit_html = render_to_string("reply_compose_inline.html", context, context_instance=req_cxt)
        json_source = {
            "body_html" : resubmit_html,
            "error" : "invalid form",
            "use_ckeditor" : True,
            "ckeditor_config" : "annotation_compose",
        }

        json = simplejson.dumps(json_source)

        return(HttpResponse(json, mimetype='application/json'))

    user = request.user
    new_comment_text = form.cleaned_data["comment_text"]

    new_comment = original_comment.reply(text=new_comment_text, user=user)

    change_modal = False
    from er.eventhandler import commentAnnotationEventHandler as caeh
    if form_type == "editor_reply":
        approval = form.cleaned_data["approval"]
        if approval == "accept":
            # change to accepted revision
            a.atype = "acptrev"
            change_modal = True
            # TODO: record the change somewhere
            caeh.notify(new_comment.model_object, action='proprev_accepted')
        elif approval == "reject":
            a.atype = "rejrev"
            change_modal = True
            caeh.notify(new_comment.model_object, action='proprev_rejected')
            pass
        elif approval == "defer":
            caeh.notify(new_comment.model_object, action='new')
            # do nothing
            pass
        else:
            # TODO: raise something, probably
            pass
    else:
        caeh.notify(new_comment.model_object, action='new')

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


@login_required_json
def preview_json(request, *args, **kwargs):
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    previews = []

    preview_template = template_loader.get_template("annotation_preview.html")

    preview_numbers = doc.paperblock_set.values('tag_id', 'annotations__atype').annotate(num=Count('annotations__id'))

    block_info = {}

    for preview_set in preview_numbers:
        atype = preview_set["annotations__atype"]
        block_id = preview_set["tag_id"]

        if block_id not in block_info:
            block_info[block_id] = {}

        if atype != None:
            block_info[block_id][atype] = preview_set["num"]
        # else continue

    for block_id in block_info:
        context = {
            "doc" : doc,
            "block_id" : block_id,
        }

        preview_data = {
            atype: [] for atype, text in Annotation.ANNOTATION_TYPES
        }

        for atype in block_info[block_id]:
            context[atype + "_list"] = preview_data[atype]
            context[atype + "_count"] = block_info[block_id][atype]

        # if context["note_count"] > 0:
        #     from django.db.models import Max
        #     latest_date = block.annotations.filter(atype='note').aggregate(Max('initial_comment__timestamp'))
        #     context["note_date"] = latest_date["initial_comment__timestamp__max"]
        # else:
        #     context["note_date"] = None

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
    summary_context["doc"] = doc
    summary_html = render_to_string("annotation_summary.html", summary_context)

    # open_questions = open_questions_for_main_doc(doc)
    # openq_context = {
    #     "doc" : doc,
    #     "open_questions" : open_questions,
    # }
    # openq_html = render_to_string("open_questions.html", openq_context)

    return_data = {
        "status" : "ok",
        "previews" : previews,
        "summary_html" : summary_html,
        # "open_questions_html" : openq_html,
    }

    json = simplejson.dumps(return_data)
    return(HttpResponse(json, mimetype='application/json'))

