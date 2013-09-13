from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse

from er.models import NewsItem, Comment

from django.db.models import Count

from er.annotation import comment

from django import forms
from django.core.urlresolvers import reverse

from ratings import attach_ratings
from follow import attach_following

import json
import urllib

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
def index_json(request, *args, **kwargs):
    req_cxt = RequestContext(request)

    offset = int(kwargs["offset"])
    this_url_name = request.resolver_match.url_name

    news_objects = NewsItem.objects.order_by('-pubdate')

    user = request.user
    num_per_load = 20
    end_limit = offset + num_per_load

    if "tag" in kwargs:
        try:
            tag_json = urllib.unquote(kwargs["tag"]).decode("utf8")
            tags = json.loads(tag_json)
        except:
            tags = []
    else:
        tags = []

    if tags != []:
        news_items = news_objects
        for tag in tags:
            news_items = news_items.filter(tags__tag_value=tag)
    else:
        news_items = news_objects.all()
        
    num_articles = news_items.all().count()
    news_items = news_items[offset:end_limit]

    for news_item in news_items:
        news_item.initial_comment = comment.fetch(news_item.comments.id)

    attach_ratings([item.initial_comment for item in news_items], user=user)
    attach_following([item.initial_comment for item in news_items], user)

    tag_change_url = reverse("news_index_tag_modal", kwargs={"tag" : "TAGS_HERE"})

    if tags == []:
        load_more_url = reverse("news_index_offset_addition", kwargs={
            "offset" : offset + num_per_load,
        })
    else:
        load_more_url = reverse("news_index_tag_offset_addition", kwargs={
            "offset" : offset + num_per_load,
            "tag" : kwargs["tag"],
        })

    if num_articles <= offset + num_per_load:
        more_to_show = False
    else:
        more_to_show = True

    context = Context({
    	"news_items" : news_items,
    	"num_articles" : num_articles,
        "tags" : tags,
        "tag_change_url" : tag_change_url,
        "more_to_show" : more_to_show,
        "load_more_url" : load_more_url,
        "num_per_load" : num_per_load,
    })

    template_name = "news_modal.html"
    if "is_addition" in kwargs and kwargs["is_addition"] == True:
        # return only additional news items if the modal has already been
        # rendered and we're just getting more entries
        template_name = "news_index.html"

    body_html = render_to_string(template_name, context, context_instance=req_cxt)

    json_str = simplejson.dumps({
        "body_html" : body_html,
        "tags" : tags,
    })

    return(HttpResponse(json_str, mimetype='application/json'))

@login_required
def comment_json(request, *args, **kwargs):
    """news item comments"""
    from er.notification import notification
    notification.mark_read(request)

    user=request.user

    req_cxt = RequestContext(request)

    item_id = kwargs["item_id"]

    news_item = NewsItem.objects.get(id=item_id)

    # in a news item, the first comment is an initial head comment
    # placed there when the news item is initialized.
    # replies are the true comments
    head_comment = comment.fetch(news_item.comments.id)
    all_comments = head_comment.thread_as_list()
    attach_ratings(all_comments, user=user)
    attach_following(all_comments, user)
    comments = all_comments[1:]

    context = Context({
        "news_item" : news_item,
        "head_comment" : head_comment,
        "comments" : comments,
    })
    body_html = render_to_string("news_comment.html", context, context_instance=req_cxt)
    json_str = simplejson.dumps({
        "body_html" : body_html,
    })

    return(HttpResponse(json_str, mimetype='application/json'))

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

    body_html = render_to_string("reply_compose_inline.html", context, context_instance=req_cxt)
    json_str = simplejson.dumps({
        "body_html" : body_html,
        "use_ckeditor" : True,
        "ckeditor_config" : "annotation_compose",
    })

    return(HttpResponse(json_str, mimetype='application/json'))

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
    
    from er.eventhandler import commentNewsEventHandler as cneh
    cneh.notify(new_comment.model_object, action='new')

    # manually manipulate the comment level one down (because it's news)
    # (will not harm underlying object)
    new_comment.level = new_comment.level - 1

    context = Context({
        "comment" : new_comment,
    })

    new_comment_html = render_to_string("reply_comment.html", context)

    json_str = simplejson.dumps({
        "html" : new_comment_html,
    })

    return(HttpResponse(json_str, mimetype='application/json'))

