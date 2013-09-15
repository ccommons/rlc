from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from er.login_decorators import login_required_json

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse

from er.models import Comment, CommentRatingPlus, CommentRatingMinus

from er.annotation import comment

from django.db.models import Count

from django.core.urlresolvers import reverse

@login_required_json
def rate_json(request, *args, **kwargs):
    req_cxt = RequestContext(request)

    user = request.user
    c = comment.fetch(kwargs["comment_id"])

    desired_action = request.resolver_match.url_name
    # desired_action = rate_plus or rate_minus

    error = None

    if c.model_object.user == user:
        error = "You can't rate your own comment."
    else:
        num_plus = c.model_object.ratings_plus.filter(user=user).count()
        num_minus = c.model_object.ratings_minus.filter(user=user).count()
    
        if (num_plus + num_minus) > 0:
            error = "You already rated this comment."
        else:
            rated_user = c.model_object.user
            if desired_action == "rate_plus":
                new_rating = CommentRatingPlus(comment=c.model_object, user=user, rated_user=rated_user)
            else: # == "rate_minus"
                new_rating = CommentRatingMinus(comment=c.model_object, user=user, rated_user=rated_user)
            new_rating.save()
            rated_already = False

    attach_ratings([c], user=user)

    context = Context({
    	"comment" : c,
    })

    body_html = render_to_string("rating_control.html", context, context_instance=req_cxt)

    json_source = {
        "body_html" : body_html,
        "user" : str(user.ratings_plus_given),
        "your_rating" : num_plus - num_minus,
        "num_plus" : num_plus,
        "num_minus" : num_minus,
    }
    if error != None:
        json_source["error"] = error

    json = simplejson.dumps(json_source)

    return(HttpResponse(json, mimetype='application/json'))

# TODO: this should go in er.annotation.py (as a class method in comment, maybe)
# attach ratings is a model-specific feature
# (this is a wrapper around Django's annotate feature)
def attach_ratings(comment_list, **kwargs):
    """attach ratings to a list of comment objects"""
    comment_dict = {}
    for c in comment_list:
        comment_dict[c.model_object.id] = c

    comment_objects = Comment.objects.filter(id__in=comment_dict.keys())
    comment_objects = comment_objects.annotate(num_plus=Count('ratings_plus'), num_minus=Count('ratings_minus'))

    # attach your own rating
    user_rated_plus = []
    user_rated_minus = []
    if "user" in kwargs:
        user = kwargs["user"]
        user_rated_plus = comment_objects.filter(ratings_plus__user=user).values_list('id', flat=True)
        user_rated_minus = comment_objects.filter(ratings_minus__user=user).values_list('id', flat=True)

    for c in comment_objects:
        comment_dict[c.id].rating = c.num_plus - c.num_minus
        if c.id in user_rated_plus:
            comment_dict[c.id].user_rated_plus = True
            comment_dict[c.id].user_rated_minus = False
        elif c.id in user_rated_minus:
            comment_dict[c.id].user_rated_plus = False
            comment_dict[c.id].user_rated_minus = True
        else:
            comment_dict[c.id].user_rated_plus = False
            comment_dict[c.id].user_rated_minus = False

