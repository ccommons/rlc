from django.core.urlresolvers import reverse

from er.models import Comment as mComment
#from er.models import Annotation as mAnnotation
from er.models import Notification as mNotification
from er.models import EvidenceReview as mEvidenceReview
from er.models import Event as mEvent

from django.contrib.auth.models import User

from er.views.annotations import atype_to_name
from er.annotation import comment

import logging
logger = logging.getLogger(__name__)

class eventHandler(object):
    """Abstract event handler base class"""

    def __config__(self):
        self._etype = ''
        self._resource_model = None
        
    def __init__(self):
        self._etype = ''
        self._resource_model = None
        #self._event = None
        self.__config__()

    @property
    def etype(self):
        if not self._etype:
            # there's probably a better exception type
            raise NotImplementedError('etype not specified')
        return self._etype

    @property
    def resource_model(self):
        return self._resource_model

    #@property
    #def event(self):
    #    return self._event

    #@event.setter
    #def event(self, event):
    #    if not self._event:
    #        self._event = event
    #    else:
    #        logger.error('event attribute can only be set once')

    @classmethod
    def cast_pks(cls, pks):
        """
        take a list of pks in strings,
        return list of pks in appropriate type depends on the resource model
        """
        raise NotImplementedError()

    def parse_notifications(self, raw_model_objs):
        """Take a list of raw notification model objects,
        return a list of notification objects with respective resource"""
        items = []
        pks = []
        for o in raw_model_objs:
            n = notification(model_object=o, event_handler=self)
            if n.event.resource_id:
                pks.append(n.event.resource_id)
            items.append(n)
        if self.resource_model:
            # get resources in bulk
            pks = self.__class__.cast_pks(pks)
            resources = self.resource_model.objects.in_bulk(pks)
            # map resources back to notification objects
            for item in items:
                if item.event.resource_id:
                    item.resource = resources.get(item.event.resource_id, None)
        return items

    def get_resource(self, resource_id):
        resource_id = self.__class__.cast_pks([resource_id])[0]
        if self.resource_model:
            try:
                return self.resource_model.objects.get(pk=resource_id)
            except:
                return None
        return None

    def construct_url(self, event):
        return ''

    def get_preview(self, event):
        return ''

#class annotationEventHandler(eventHandler):
#    def __config__(self):
#        self._etype = 'annotation'
#        self._resource_model = mAnnotation
#
#    @classmethod
#    def cast_pks(cls, pks):
#        return map(lambda x: int(x), pks)

class commentEventHandler(eventHandler):
    def __config__(self):
        self._resource_model = mComment
        
    def __init__(self):
        eventHandler.__init__(self)

    @classmethod
    def cast_pks(cls, pks):
        return map(lambda x: int(x), pks)

    def create_comment_obj(self, event):
        if event and event.resource:
            c = comment()
            c.model_object = event.resource
            c.init_from_model()
            return c
        return None

class commentAnnotationEventHandler(commentEventHandler):
    def __config__(self):
        commentEventHandler.__config__(self)
        self._etype = 'comment_annotation'

    def construct_url(self, event):
        c = self.create_comment_obj(event)
        if not c:
            return ''
        try:
            # an annotation
            a = c.root.model_object.annotation
            return reverse('annotation_one_of_all', kwargs={'doc_id':a.er_doc.id,'annotation_id':a.id,})
        except Exception, e:
            logger.error(e)
            pass
        return ''

    def get_preview(self, event):
        c = self.create_comment_obj(event)
        if not c:
            return ''
        comment_text = c.text[:100]
        if c.is_root():
            try:
                a = c.annotation
                if a.doc_block:
                    return a.doc_block.preview_text
                else:
                    return comment_text
            except:
                pass
        return comment_text

class commentNewsEventHandler(commentEventHandler):
    def __config__(self):
        commentEventHandler.__config__(self)
        self._etype = 'comment_news'

    def construct_url(self, event):
        c = self.create_comment_obj(event)
        if not c:
            return ''
        try:
            a = c.root.model_object.news
            # XXX TODO
            return ''
        except Exception, e:
            logger.error(e)
            pass
        return ''

    def get_preview(self, event):
        c = self.create_comment_obj(event)
        if not c:
            return ''
        comment_text = c.text[:100]
        if c.is_root():
            try:
                a = c.news
                # XXX TODO
                return comment_text
            except:
                pass
        return comment_text

class EvidenceReviewEventHandler(eventHandler):
    def __config__(self):
        self._etype = 'er'
        self._resource_model = mEvidenceReview

    @classmethod
    def cast_pks(cls, pks):
        return map(lambda x: int(x), pks)

    def construct_url(self, event):
        if not event or not event.resource:
            return ''
        return reverse('doc_full_view', doc_id=event.resource.id)

    def get_preview(self, event):
        if not event or not event.resource:
            return ''
        return event.resource.title

# XXX TODO: make it a subclass of dict, verify key with etype of handler whenever a key/value pair is set
EVENT_TYPE_HANDLER_MAP = {
    #'annotation' : annotationEventHandler,
    'comment_annotation' : commentAnnotationEventHandler,
    'comment_news' : commentNewsEventHandler,
    'er' : EvidenceReviewEventHandler,
    #'user' : UserEventHandler,
}

class event(object):
    """Represents an event"""
    MODEL = mEvent

    def __init__(self, *args, **kwargs):
        self._event_handler = None
        self.timestamp = None
        self.action = ''
        self.remarks = ''
        self._resource_id = ''

        self._resource = None
        self._model_object = None

        if 'event_handler' in kwargs and kwargs['event_handler']:
            if not isinstance(kwargs['event_handler'], eventHandler):
                raise TypeError("event_handler must be an instance of eventHandler")
            self._event_handler = kwargs['event_handler']

        if 'model_object' in kwargs:
            if isinstance(kwargs['model_object'], self.__class__.MODEL):
                if self.event_handler:
                    if not self.event_handler.etype == kwargs['model_object'].etype:
                        raise TypeError("model object etype does not match event handler etype")
                else:
                    # create event handler
                    self._event_handler = EVENT_TYPE_HANDLER_MAP[kwargs['model_object']]()
                self._model_object = kwargs['model_object']
                # init from model
                self.timestamp = self._model_object.timestamp
                self.action = self._model_object.action
                self.resource_id = self._model_object.resource_id
                self.remarks = self._model_object.remarks
            else:
                raise TypeError('model_object must be an instance of %s' % type(self.__class.__MODEL))

        # at this point, _event_handler must have been set
        if not self.event_handler:
            raise Exception("event handler not set")

        if 'resource' in kwargs:
            self.resource = kwargs['resource']

        if not self._model_object:
            # create one
            action = kwargs.get('action', None)
            valid_actions = [a[0] for a in self.__class__.MODEL.ACTIONS]
            if action and action not in valid_actions:
                raise ValueError("action must be None or one of %s" % str(valid_actions))
            res_id = (self.resource and str(self.resource.pk)) or str(kwargs.get('resource_id', ''))
            remarks = kwargs.get('remarks', '')
            self._model_object = self.__class__.MODEL(
                etype = self.event_handler.etype,
                action = action,
                resource_id = res_id,
                remarks = remarks,
            )
            self._model_object.save()

        #at this point, model_object must have been created

    @property
    def model_object(self):
        return self._model_object

    @property
    def etype(self):
        return self._event_handler.etype

    @property
    def event_handler(self):
        return self._event_handler

    @property
    def resource_id(self):
        # get id from resource if one exists
        if not self._resource_id and self._resource:
            self.resource_id = self._resource.pk
        return self._resource_id

    @resource_id.setter
    def resource_id(self, rid):
        if self.resource:
            if str(rid) != str(self.resource.pk):
                raise ValueError("resource_id %s does not match resource pk %s" % (rid, self.resource.pk))
        # do not automatically set resource from resource_id to allow bulk retrival of resources
        self._resource_id = str(rid)
    
    def unset_resource(self):
        self._resource_id = ''
        self._resource = None

    @property
    def resource(self):
        # get resource if id and etype are set
        if not self._resource and self._resource_id:
            self.resource = self.event_handler.get_resource(self._resource_id)
        return self._resource

    @resource.setter
    def resource(self, obj):
        if not obj:
            self._resource = None
            return
        if not isinstance(obj, self.event_handler.resource_model):
            raise TypeError("%s is not an instance of %s" %(obj, type(EVENT_TYPE[self.etype].resource_model)))
        self._resource = obj
        # check broken link
        if self.resource_id:
            if str(obj.pk) != self.resource_id:
                self._resource = None
        else:
            # automatically assign resource_id from obj
            self.resource_id = obj.pk

    @property
    def url(self):
        return self.event_handler.construct_url(self)

    @property
    def preview(self):
        return self.event_handler.get_preview(self)

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
                        subject = 'replied to your %s.' % atype_to_name(root.annotation.atype)
                    except:
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
        return self.event.preview

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
