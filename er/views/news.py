from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse

from er.models import NewsItem, Comment

from er.annotation import comment

from django import forms
from django.core.urlresolvers import reverse

@login_required
def index(request, *args, **kwargs):
    """index page"""
    req_cxt = RequestContext(request)
    news_items = NewsItem.objects.all()

    override_ckeditor = True;

    context = Context({
	"doctitle" : "Melanoma RLC: News",
    	"news_items" : news_items,
        "tab" : "news",
        "override_ckeditor" : override_ckeditor,
    })

    return(render_to_response("news.html", context, context_instance=req_cxt))

@login_required
def comment_json(request, *args, **kwargs):
    """news item comments"""
    req_cxt = RequestContext(request)

    item_id = kwargs["item_id"]

    news_item = NewsItem.objects.get(id=item_id)

    # in a news item, the first comment is an initial head comment
    # placed there when the news item is initialized.
    # replies are the true comments
    head_comment = comment.fetch(news_item.comments.id)
    all_comments = head_comment.thread_as_list()
    comments = all_comments[1:]

    modal_id = "modal-news-{0}".format(item_id)

    context = Context({
        "modal_id" : modal_id,
        "news_item" : news_item,
        "head_comment" : head_comment,
        "comments" : comments,
    })
    body_html = render_to_string("news_comment.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
        "body_html" : body_html,
        "modal_id" : modal_id,
    })

    return(HttpResponse(json, mimetype='application/json'))

class NewsReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [] 

    comment_text = forms.CharField(widget=forms.Textarea())


@login_required
def reply_json(request, *args, **kwargs):
    """news item -- compose a reply"""
    req_cxt = RequestContext(request)

    form = NewsReplyForm()

    action = reverse("news_reply_new", kwargs={
                 "comment_id" : kwargs["comment_id"],
             })

    context = Context({
        "form" : form,
        "form_action" : action,
    })

    body_html = render_to_string("news_reply.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
        "body_html" : body_html,
        "use_ckeditor" : True,
        "ckeditor_config" : "annotation_compose",
    })

    return(HttpResponse(json, mimetype='application/json'))

@login_required
@require_POST
def reply_new_json(request, *args, **kwargs):
    original_comment = comment.fetch(id=kwargs["comment_id"])

    form = NewsReplyForm(request.POST)

    if form.is_valid():
        # TODO: error out if invalid
        pass

    user = request.user
    new_comment_text = form.cleaned_data["comment_text"]
    
    new_comment = original_comment.reply(text=new_comment_text, user=user)

    json = simplejson.dumps({
        "html" : new_comment_text,
    })

    return(HttpResponse(json, mimetype='application/json'))

