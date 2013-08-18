from er.models import Comment as mComment
from er.models import Annotation as mAnnotation
from er.models import Notification as mNotification
from er.models import EvidenceReview as mEvidenceReview
from er.models import Event as mEvent

from django.contrib.auth.models import User

class eventHandler(object):
    """Abstract event handler base class"""

    def __config__(self):
        self._etype = ''
        self._resource_model = None
        
    def __init__(self):
        self._etype = ''
        self._resource_model = None
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

class annotationEventHandler(eventHandler):
    def __config__(self):
        self._etype = 'annotation'
        self._resource_model = mAnnotation

    @classmethod
    def cast_pks(cls, pks):
        return map(lambda x: int(x), pks)

class commentEventHandler(eventHandler):
    def __config__(self):
        self._etype = 'comment'
        self._resource_model = mComment

    @classmethod
    def cast_pks(cls, pks):
        return map(lambda x: int(x), pks)

class EvidenceReviewEventHandler(eventHandler):
    def __config__(self):
        self._etype = 'er'
        self._resource_model = mEvidenceReview

    @classmethod
    def cast_pks(cls, pks):
        return map(lambda x: int(x), pks)


# XXX make it a subclass of dict, verify key with etype of handler whenever a key/value pair is set
EVENT_TYPE_HANDLER_MAP = {
    'annotation' : annotationEventHandler,
    'comment' : commentEventHandler,
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

    @classmethod
    def count(cls, user):
        return cls.MODEL.objects.filter(user, shown=False, read=False).count()
