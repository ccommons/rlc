from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from er.login_decorators import login_required_json
from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse

from er.models import Notification
from er.eventhandler import EVENT_TYPE_HANDLER_MAP
from er.notification import notification

import logging
logger = logging.getLogger(__name__)

def parse_notifications(raw):
    items = []
    etypes = {}
    for n in raw:
        if n.event.etype in etypes:
            etypes[n.event.etype].append(n)
        else:
            etypes[n.event.etype] = [n]

    for etype in etypes:
        if etype in EVENT_TYPE_HANDLER_MAP:
            handler = EVENT_TYPE_HANDLER_MAP[etype]()
            notifications = []
            for model_obj in etypes[etype]:
                n = notification(model_object=model_obj, event_handler=handler)
                notifications.append(n)
            items += handler.parse_notifications(notifications)
        else:
            logger.error('etype %s not in EVENT_TYPE_HANDLER_MAP' % etype)

    return items

def get_notifications(request):
    # load all notifications of the user
    notifications_all = Notification.objects.filter(user=request.user)

    # now, pick only the 10 most recent and relevant
    notifications = notifications_all.all().exclude(event__action='revised').order_by('-event__timestamp')[:10]

    all_items = parse_notifications(notifications)
    all_items = sorted(all_items, key=lambda n:n.timestamp, reverse=True)


    context = Context({
        "override_ckeditor" : True,
        "items" : all_items,
    })

    # mark all unshown notifications shown (regardless of if they're being
    # displayed or not)
    # XXX need try/catch?
    notifications_unshown = notifications_all.all().exclude(shown=True)
    notifications_unshown.update(shown=True)

    return context

@login_required
def notifications_menu(request):
    """notification menu shows each notification item"""
    context = get_notifications(request)
    req_cxt = RequestContext(request)
    return(render_to_response("notification_page.html", context, context_instance=req_cxt))

@login_required_json
def notifications_json(request):
    """notification menu shows each notification item"""
    context = get_notifications(request)
    req_cxt = RequestContext(request)
    body_html = render_to_string("notification_menu.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
    })
    return (HttpResponse(json, mimetype='application/json'))

@login_required_json
def notifications_count_json(request):
    """notification count for the user"""
    req_cxt = RequestContext(request)
    user = request.user

    count = notification.count(user)
    json = simplejson.dumps({
    	"count" : count,
    })
    return (HttpResponse(json, mimetype='application/json'))
