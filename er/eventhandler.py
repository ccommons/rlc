from er.models import Comment as mComment
from er.models import EvidenceReview as mEvidenceReview
from er.annotation import comment
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
    'comment_annotation' : commentAnnotationEventHandler,
    'comment_news' : commentNewsEventHandler,
    'er' : EvidenceReviewEventHandler,
    #'user' : UserEventHandler,
}


