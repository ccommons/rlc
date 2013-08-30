from er.models import Event as mEvent
from er.eventhandler import EVENT_TYPE_HANDLER_MAP, eventHandler

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


