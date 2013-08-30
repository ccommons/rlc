from er.models import Comment as mComment
from er.models import EvidenceReview as mEvidenceReview
from django.core.urlresolvers import reverse

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

    @classmethod
    def cast_pks(cls, pks):
        """
        take a list of pks in strings,
        return list of pks in appropriate type depends on the resource model
        """
        raise NotImplementedError()

    def parse_notifications(self, notifications):
        """Take a list of notification objects,
        return a list of notification objects with respective resource"""
        items = []
        pks = []
        for n in notifications:
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

    @classmethod
    def register_event(cls, *args, **kwargs):
        """notification API
           wrapper for create_event(), silent all exceptions
           returns an event object
        """
        try:
            return cls.create_event(*args, **kwargs)
        except Exception, ex:
            logger.error(ex)
            return None

    @classmethod
    def create_event(cls, *args, **kwargs):
        """ subclasses must implement """
        return None

    @classmethod
    def match_request(cls, event_model, request):
        """
        subclasses should implement
        takes an Event model object and a HttpRequest object
        returns True if they match, False otherwise
        """
        return False

class commentEventHandler(eventHandler):
    def __config__(self):
        self._resource_model = mComment
        
    def __init__(self):
        eventHandler.__init__(self)

    @classmethod
    def cast_pks(cls, pks):
        return map(lambda x: int(x), pks)

    def create_comment_obj(self, event):
        from er.annotation import comment
        if event and event.resource:
            c = comment()
            c.model_object = event.resource
            c.init_from_model()
            return c
        return None

    @classmethod
    def create_event(cls, *args, **kwargs):
        """
        must take one positional argument (the comment model object),
        optional keyword argument 'action' and 'remarks'
        """
        from er.event import event
        resource = args[0]
        event_handler=cls()
        event_kwargs = dict(event_handler=event_handler, resource=resource)
        if 'action' in kwargs:
            event_kwargs['action'] = kwargs['action']
        if 'remarks' in kwargs:
            event_kwargs['remarks'] = kwargs['remarks']
        e = event(**event_kwargs)
        return e

class commentAnnotationEventHandler(commentEventHandler):
    def __config__(self):
        commentEventHandler.__config__(self)
        self._etype = 'comment_annotation'

    def construct_url(self, event):
        c = self.create_comment_obj(event)
        a = c.root.model_object.annotation
        return reverse('annotation_one_of_all', kwargs={'doc_id':a.er_doc.id,'annotation_id':a.id,})

    def get_preview(self, event):
        c = self.create_comment_obj(event)
        comment_text = c.text[:100]
        if c.is_root():
            a = c.model_object.annotation
            if a.doc_block:
                return a.doc_block.preview_text
        return comment_text

    @classmethod
    def match_request(cls, event_model, request):
        """
        subclasses should implement
        takes an Event model object and a HttpRequest object
        returns True if they match, False otherwise
        """
        doc_id = int(request.resolver_match.kwargs.get('doc_id', ''))
        annotation_id = int(request.resolver_match.kwargs.get('annotation_id', ''))
        url_name = request.resolver_match.url_name
        from er.event import event
        handler = cls()
        e = event(model_object=event_model, event_handler=handler)
        try:
            c = handler.create_comment_obj(e)
            a = c.root.model_object.annotation
            if doc_id == a.er_doc.id and annotation_id == a.id and url_name == 'annotation_one_of_all':
                return True
        except:
            pass
        return False

class proprevApprovedEventHandler(commentAnnotationEventHandler):
    def __config__(self):
        commentAnnotationEventHandler.__config__(self)
        self._etype = 'proprev_approved'

    def get_preview(self, event):
        c = self.create_comment_obj(event)
        return c.root.model_object.annotation.doc_block.preview_text

class commentNewsEventHandler(commentEventHandler):
    def __config__(self):
        commentEventHandler.__config__(self)
        self._etype = 'comment_news'

    def construct_url(self, event):
        c = self.create_comment_obj(event)
        a = c.root.model_object.news
        # XXX TODO
        return ''

    def get_preview(self, event):
        c = self.create_comment_obj(event)
        comment_text = c.text[:100]
        if c.is_root():
            a = c.news
            # XXX TODO
            return comment_text
        return comment_text

class EvidenceReviewEventHandler(eventHandler):
    def __config__(self):
        self._etype = 'er'
        self._resource_model = mEvidenceReview

    @classmethod
    def cast_pks(cls, pks):
        return map(lambda x: int(x), pks)

    def construct_url(self, event):
        return reverse('doc_full_view', doc_id=event.resource.id)

    def get_preview(self, event):
        return event.resource.title

    @classmethod
    def create_event(cls, *args, **kwargs):
        """
        must take one positional argument (the EvidenceReview model object),
        optional keyword argument 'action' and 'remarks'
        """
        from er.event import event
        resource = args[0]
        event_handler=cls()
        event_kwargs = dict(event_handler=event_handler, resource=resource)
        if 'action' in kwargs:
            event_kwargs['action'] = kwargs['action']
        if 'remarks' in kwargs:
            event_kwargs['remarks'] = kwargs['remarks']
        e = event(**event_kwargs)
        return e

    @classmethod
    def match_request(cls, event_model, request):
        """
        subclasses should implement
        takes an Event model object and a HttpRequest object
        returns True if they match, False otherwise
        """
        doc_id = request.resolver_match.kwargs.get('doc_id', '')
        url_name = request.resolver_match.url_name
        try:
            if doc_id == event_model.resource_id and url_name == 'doc_full_view':
                return True
        except:
            pass
        return False

# XXX TODO: make it a subclass of dict, verify key with etype of handler whenever a key/value pair is set
EVENT_TYPE_HANDLER_MAP = {
    'comment_annotation' : commentAnnotationEventHandler,
    #'comment_news' : commentNewsEventHandler,
    'proprev_approved' : proprevApprovedEventHandler,
    'er' : EvidenceReviewEventHandler,
    #'user' : UserEventHandler,
}
