from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse

from er.models import Comment, CommentFollower

from er.annotation import comment

from django.db.models import Count

from django.core.urlresolvers import reverse

@login_required
def follow_json(request, *args, **kwargs):
    req_cxt = RequestContext(request)

    user = request.user

    c = comment.fetch(kwargs["comment_id"])
    attach_following([c], user=user)

    desired_action = request.resolver_match.url_name
    # desired_action = follow_json or unfollow_json

    error = None

    if c.model_object.user == user:
        error = "You don't need to follow your own comment."
    else:
        # following?
        if desired_action == 'follow_json':
            if not c.following:
                follow = CommentFollower(comment=c.model_object, user=user)
                follow.save()
        elif desired_action == 'unfollow_json':
            if c.following:
                follow = CommentFollower.objects.get(comment=c.model_object, user=user)
                follow.delete()

        # something with desired_action
    
    attach_following([c], user=user)

    context = Context({
    	"comment" : c,
    })

    body_html = render_to_string("follow_control.html", context, context_instance=req_cxt)

    json_source = {
        "body_html" : body_html,
        "following" : c.following,
    }

    if error != None:
        json_source["error"] = error

    json = simplejson.dumps(json_source)

    return(HttpResponse(json, mimetype='application/json'))

# TODO: this should go in er.annotation.py (as a class method in comment, maybe)
# attach ratings is a model-specific feature
# (this is a wrapper around Django's annotate feature)
def attach_following(comment_list, user):
    """attach ratings to a list of comment objects"""
    comment_dict = {}
    for c in comment_list:
        comment_dict[c.model_object.id] = c
        c.following = False

    comment_objects = Comment.objects.filter(id__in=comment_dict.keys())
    comment_objects = comment_objects.filter(following__user=user)

    for c in comment_objects:
        if c.id in comment_dict:
            comment_dict[c.id].following = True

