from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
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
    notifications = Notification.objects.filter(user=request.user)

    all_items = parse_notifications(notifications)
    all_items = sorted(all_items, key=lambda n:n.timestamp, reverse=True)

    # group items by unread/read
    unread_items = []
    read_items = []
    for item in all_items:
        if item.read:
            read_items.append(item)
        else:
            unread_items.append(item)

    context = Context({
        "override_ckeditor" : True,
        "unread" : unread_items,
        "read" : read_items,
    })

    # mark all notifications shown
    # XXX need try/catch?
    notifications.update(shown=True)

    return context

@login_required
def notifications_menu(request):
    """notification menu shows each notification item"""
    context = get_notifications(request)
    req_cxt = RequestContext(request)
    return(render_to_response("notification_menu.html", context, context_instance=req_cxt))

@login_required
def notifications_json(request):
    """notification menu shows each notification item"""
    context = get_notifications(request)
    req_cxt = RequestContext(request)
    body_html = render_to_string("notification_menu.html", context, context_instance=req_cxt)
    popover_id = 'popover-notification'
    json = simplejson.dumps({
    	"body_html" : body_html,
        "popover_id" : popover_id,
    })
    return (HttpResponse(json, mimetype='application/json'))
