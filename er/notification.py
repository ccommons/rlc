from er.models import Notification as mNotification
from er.event import event

import HTMLParser

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
            'note' : 'attached a note.',
            'openq' : 'asked an open question.',
        }
        subject = ''
        #if self.event.etype == 'annotation':
        #    if self.event.resource:
        #        subject = annotation_subject.get(self.event.resource.atype, '')
        #elif self.event.etype == 'comment':
        if self.event.etype == 'comment_annotation':
            c = self.event.event_handler.create_comment_obj(self.event)
            if not c:
                return ''
            subject = 'replied to your comment.'
            try:
                # an annotation
                subject = annotation_subject.get(c.model_object.annotation.atype, '')
            except:
                # a reply
                root = c.root
                if root.user == self.user:
                    try:
                        from er.views.annotations import atype_to_name
                        subject = 'replied to your %s.' % atype_to_name(root.model_object.annotation.atype).lower()
                    except Exception, ex:
                        logger.error(ex)
                        pass
        elif self.event.etype == 'comment_news':
            # XXX TODO
            pass
        elif self.event.etype == 'er':
            if self.event.action in ['revised', 'updated']:
                subject = 'The Evidence Review is revised.'
            elif self.event.action == 'published':
                subject = "The Evidence Review is published."
        elif self.event.etype == 'user':
            subject = "joined the system."
        return subject

    @property
    def context(self):
        html_parser = HTMLParser.HTMLParser()
        return html_parser.unescape(self.event.preview)

    @property
    def url(self):
        return self.event.url

    @property
    def subject_user(self):
        if self.event.etype in ['comment_annotation', 'comment_news']:
            try:
                return self.event.resource.user
            except:
                return None
        elif self.event.etype == 'user':
            return self.event.resource
        return None

    @classmethod
    def count(cls, user):
        return cls.MODEL.objects.filter(user, shown=False, read=False).count()
