from er.models import Notification as mNotification
from er.emailnotification import emailNotification
from er.event import event
import json
from django.contrib.auth.models import User

import logging
logger = logging.getLogger(__name__)

class notification(object):
    """Represents a notification"""
    MODEL = mNotification

    def __init__(self, *args, **kwargs):
        self.user = None
        self.event = None
        self.shown = False
        self.read = False
        self.model_object = None

        # create new notification if there are event and user args
        if 'event' in kwargs and 'user' in kwargs:
            if isinstance(kwargs['event'], event) and kwargs['event'].model_object:
                self.model_object = self.__class__.MODEL(
                    user=kwargs['user'],
                    event=kwargs['event'].model_object,
                )
                self.model_object.save()
                self.user = kwargs['user']
                self.event = kwargs['event']
                # also create an email notification
                emailNotification(event=self.event, user=self.user)

        if 'model_object' in kwargs:
            if isinstance(kwargs['model_object'], self.__class__.MODEL):
                self.model_object = kwargs['model_object']
                self.user = self.model_object.user
                self.shown = self.model_object.shown
                self.read = self.model_object.read
                self.event = event(model_object=self.model_object.event, event_handler=kwargs.get('event_handler', None))
            else:
                raise TypeError('model_object must be an instance of %s' % type(self.__class__.MODEL))

        # at this point, user and event mush have been set
        if not self.user:
            raise Exception("user not set")
        if not self.event:
            raise Exception("event not set")

    @property
    def subject(self):
        annotation_subject = {
            'proprev' : 'proposed a revision.',
            'rev' : 'proposed a revision.',
            'note' : 'attached a note.',
            'openq' : 'asked an open question.',
        }
        subject = ''
        if self.event.etype == 'comment_annotation':
            c = self.event.event_handler.create_comment_obj(self.event)
            if not c:
                return ''
            subject = 'replied to a thread of your interest.'
            try:
                # an annotation
                atype = c.model_object.annotation.atype
                if self.event.action == 'shared':
                    return ' '.join([
                        'shared',
                        (atype=='openq' and 'an' or 'a'),
                        atype_to_name(atype),
                        'with you.'
                    ])
                else:
                    return annotation_subject.get(atype, '')
            except:
                # a reply
                root = c.root
                if self.event.action == 'proprev_accepted':
                    if root.user == self.user:
                        return 'Your proposed revision is accepted.'
                    else:
                        return 'The propesed revision is accepted.'
                elif self.event.action == 'proprev_rejected':
                    if root.user == self.user:
                        return 'Your proposed revision is rejected.'
                    else:
                        return 'The propesed revision is rejected.'
                elif self.event.action == 'shared':
                    return 'shared a comment with you.'
                else:
                    # a regular reply
                    if root.user == self.user:
                        try:
                            from er.views.annotations import atype_to_name
                            return 'replied to your %s.' % atype_to_name(root.model_object.annotation.atype).lower()
                        except Exception, ex:
                            logger.error(ex)
                            pass
        elif self.event.etype == 'comment_news':
            if self.event.action == 'shared':
                return 'shared a comment with you.'
            else:
                return 'replied to a thread of your interest.'
        elif self.event.etype == 'er':
            if self.event.action == 'shared':
                return 'shared an Evidence Review with you.'
            if self.event.action in ['revised', 'updated']:
                return 'The Evidence Review is revised.'
            elif self.event.action == 'published':
                return "The Evidence Review is published."
        elif self.event.etype == 'user':
            return "joined the system."
        return subject

    @property
    def context(self):
        try:
            return self.event.preview
        except Exception,ex:
            logger.error(ex)
            return ''

    @property
    def url(self):
        try:
            return self.event.url
        except Exception,ex:
            logger.error(ex)
            return ''

    @property
    def url_json(self):
        try:
            return self.event.url_json
        except Exception,ex:
            logger.error(ex)
            return ''

    @property
    def subject_user(self):
        try:
            if self.event.action == 'shared':
                try:
                    remarks = json.loads(self.event.remarks)
                    return User.objects.get(id=remarks['sharer'])
                except:
                    return None
            if self.event.etype in ['comment_annotation', 'comment_news']:
                if self.event.action in ['proprev_accepted', 'proprev_rejected']:
                    return None
                else:
                    return self.event.resource.user
            elif self.event.etype == 'user':
                return self.event.resource
        except Exception, ex:
            logger.error(ex)
        return None

    @property
    def timestamp(self):
        try:
            return self.event.timestamp
        except Exception, ex:
            logger.error(ex)
            return None

    @property
    def etype(self):
        try:
            return self.event.etype
        except Exception, ex:
            logger.error(ex)
            return ''

    @classmethod
    def count(cls, user):
        try:
            return cls.MODEL.objects.filter(user=user, shown=False, read=False).count()
        except Exception, ex:
            logger.error(ex)
            return 0

    # XXX TODO
    @classmethod
    def mark_read(cls, request):
        """ notification API """
        try:
            from er.eventhandler import EVENT_TYPE_HANDLER_MAP as handlers
            if not request.user.is_authenticated():
                return
            # look up notifications for the user
            model_objs = mNotification.objects.filter(user=request.user, read=False)
            # match each event to the request, mark read if match
            for n in model_objs:
                try:
                    handler_cls = handlers.get(n.event.etype, None)
                    if handler_cls:
                        if handler_cls.match_request(n.event, request):
                            n.read = True
                            n.save()
                except Exception, ex:
                    logger.error(ex)
                    continue
        except Exception, ex:
            logger.error(ex)
        return
