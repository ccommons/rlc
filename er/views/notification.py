from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required

from er.models import Notification
from er.notification import EVENT_TYPE_HANDLER_MAP

def parse_notifications(notifications):
    items = []
    etypes = {}
    for n in notifications:
        if n.event.etype in etypes:
            etypes[n.event.etype].append(n)
        else:
            etypes[n.event.etype] = [n]

    for etype in etypes:
        if etype in EVENT_TYPE_HANDLER_MAP:
            handler = EVENT_TYPE_HANDLER_MAP[etype]()
            items += handler.parse_notifications(etypes[etype])
        else:
            # debug message
            pass

    return items

@login_required
def notifications_menu(request):
    """notification menu shows each notification item"""
    req_cxt = RequestContext(request)

    # load all notifications of the user
    notifications = Notification.objects.filter(user=request.user)

    all_items = parse_notifications(notifications)

    # group items by unread/read
    unread_items = []
    read_items = []
    for item in all_items:
        if item.read:
            read_items.append(item)
        else:
            unread_items.append(item)

    context = Context({
        "unread" : unread_items,
        "read" : read_items,
    })

    # mark all notifications shown
    # XXX need try/catch?
    notifications.update(shown=True)

    return(render_to_response("notification_menu.html", context, context_instance=req_cxt))
