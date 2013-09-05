from er.models import Comment as mComment
from er.models import EvidenceReview as mEvidenceReview
from er.models import CommentFollower as mCommentFollower
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

    @classmethod
    def make_notifications(cls, event, **kwargs):
        """
        notification API
        takes an event object
        optional users kwarg
        if users kwarg is present, make notification for the users specified,
        otherewise, it determines who should get the notification and make them
        """
        try:
            if 'users' in kwargs:
                users = kwargs['users']
            else:
                users = cls.collect_notification_recipients(event)
            if not users:
                return
            from er.notification import notification
            for user in set(users):
                try:
                    notification(event=event, user=user)
                except Exception, ex:
                    logger.error(ex)
                    continue
        except Exception, ex:
            logger.error(ex)

    @classmethod
    def collect_notification_recipients(cls, event):
        """
        subclass should implement
        determines who should get the notification depending on the event
        returns an iterable of users
        """
        return []

    @classmethod
    def notify(cls, *args, **kwargs):
        """
        notification API
        shorthand for create_event() and make_notifications()
        the kwargs are shared between the two methods
        """
        try:
            event = cls.create_event(*args, **kwargs)
            cls.make_notifications(event, **kwargs)
        except Exception, ex:
            logger.error(ex)

    @classmethod
    def match_email_preference(cls, preferences, event):
        """
        subclass should implement
        match the event with email preferences
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

    @classmethod
    def create_comment_obj(cls, event):
        try:
            from er.annotation import comment
            if event and event.resource:
                return comment.fetch(event.resource.id)
        except Exception, ex:
            logger.error(ex)
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

    @classmethod
    def collect_notification_recipients(cls, event):
        """
        determines who should get the notification depending on the comment
        returns a list of users minus the comment owner
        """
        output = set()

        comment = cls.create_comment_obj(event)
        # everybody gets notification on new annotation
        if comment.is_root():
            from django.contrib.auth.models import User as mUser
            users = mUser.objects.all()
            for u in users:
                output.add(u)
        else:
            ancestors = comment.ancestors or []

            # get each one back up the thread
            for c in ancestors:
                output.add(c.user)

            # add followers
            for c in ancestors:
                followers = mCommentFollower.objects.filter(comment=c.model_object)
                for f in followers:
                    output.add(f.user)
                    
        if comment.user in output:
            output.remove(comment.user)
        return output

class commentAnnotationEventHandler(commentEventHandler):
    def __config__(self):
        commentEventHandler.__config__(self)
        self._etype = 'comment_annotation'

    def construct_url(self, event):
        c = self.__class__.create_comment_obj(event)
        a = c.root.model_object.annotation
        return reverse('annotation_one_of_all', kwargs={'doc_id':a.er_doc.id,'annotation_id':a.id,})

    def get_preview(self, event):
        c = self.__class__.create_comment_obj(event)
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
        #doc_id = int(request.resolver_match.kwargs.get('doc_id', '-1'))
        annotation_id = int(request.resolver_match.kwargs.get('annotation_id', '-1'))
        #url_name = request.resolver_match.url_name
        from er.event import event
        handler = cls()
        e = event(model_object=event_model, event_handler=handler)
        try:
            c = handler.__class__.create_comment_obj(e)
            a = c.root.model_object.annotation
            if annotation_id == a.id:# and doc_id == a.er_doc.id and url_name == 'annotation_one_of_all':
                return True
        except:
            pass
        return False

    @classmethod
    def match_email_preference(cls, preferences, event):
        """
        match the event with email preferences
        """
        if event and event.resource:
            try:
                c = cls.create_comment_obj(event)
                if c.is_root():
                    """nobody gets email for new annotation"""
                    return False
                if c.root.user == preferences.user:
                    """ activity on my note/rev/oq """
                    atype = c.root.model_object.annotation.atype
                    if atype in ['proprev', 'rev'] and preferences.activity_rev:
                        return True
                    elif atype == 'note' and preferences.activity_note:
                        return True
                    elif atype == 'openq' and preferences.activity_openq:
                        return True
                else:
                    """ check if the preferences' user one of the ancestor of the event """
                    if preferences.user in [a.user for a in c.ancestors]:
                        """ activity on my comment """
                        if preferences.activity_comment:
                            return True
            except Exception, ex:
                logger.error(ex)
        return False

class proprevAcceptedEventHandler(commentAnnotationEventHandler):
    def __config__(self):
        commentAnnotationEventHandler.__config__(self)
        self._etype = 'proprev_accepted'

    def get_preview(self, event):
        c = self.__class__.create_comment_obj(event)
        try:
            return c.root.model_object.annotation.doc_block.preview_text
        except:
            return c.root.model_object.text[:100]

class commentNewsEventHandler(commentEventHandler):
    def __config__(self):
        commentEventHandler.__config__(self)
        self._etype = 'comment_news'

    def construct_url(self, event):
        c = self.__class__.create_comment_obj(event)
        n = c.root.model_object.newsitem
        return reverse('news_comment', kwargs={'item_id':n.id,})

    def get_preview(self, event):
        c = self.__class__.create_comment_obj(event)
        comment_text = c.text[:100]
        return comment_text

    @classmethod
    def match_request(cls, event_model, request):
        """
        subclasses should implement
        takes an Event model object and a HttpRequest object
        returns True if they match, False otherwise
        """
        item_id = int(request.resolver_match.kwargs.get('item_id', '-1'))
        #url_name = request.resolver_match.url_name
        from er.event import event
        handler = cls()
        e = event(model_object=event_model, event_handler=handler)
        try:
            c = handler.__class__.create_comment_obj(e)
            n = c.root.model_object.newsitem
            if item_id == n.id:# and url_name == 'news_comment':
                return True
        except:
            pass
        return False

    @classmethod
    def match_email_preference(cls, preferences, event):
        """
        match the event with email preferences
        """
        if event and event.resource:
            try:
                c = cls.create_comment_obj(event)
                """ check if the preferences' user one of the ancestor of the event """
                if not c.is_root() and preferences.user in [a.user for a in c.ancestors]:
                    """ activity on my comment """
                    if preferences.activity_comment:
                        return True
            except Exception, ex:
                logger.error(ex)
        return False

class EvidenceReviewEventHandler(eventHandler):
    def __config__(self):
        self._etype = 'er'
        self._resource_model = mEvidenceReview

    @classmethod
    def cast_pks(cls, pks):
        return map(lambda x: int(x), pks)

    def construct_url(self, event):
        return reverse('document_fullview', kwargs=dict(doc_id=event.resource.id))

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
    def collect_notification_recipients(cls, event):
        """
        all users get notification 
        """
        output = set()

        from django.contrib.auth.models import User as mUser
        users = mUser.objects.all()
        for u in users:
            output.add(u)

        return output

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
            if doc_id == event_model.resource_id and url_name == 'document_fullview':
                return True
        except:
            pass
        return False

    @classmethod
    def match_email_preference(cls, preferences, event):
        """
        match the event with email preferences
        """
        if event and event.resource:
            try:
                print event.action
                print preferences
                if event.action == 'updated' and preferences.er_updated:
                    return True
                elif event.action == 'revised' and preferences.er_revised:
                    return True
                elif event.action == 'published' and preferences.er_published:
                    return True
            except Exception, ex:
                logger.error(ex)
        return False

# XXX TODO: make it a subclass of dict, verify key with etype of handler whenever a key/value pair is set
EVENT_TYPE_HANDLER_MAP = {
    'comment_annotation' : commentAnnotationEventHandler,
    'comment_news' : commentNewsEventHandler,
    'proprev_accepted' : proprevAcceptedEventHandler,
    'er' : EvidenceReviewEventHandler,
    #'user' : UserEventHandler,
}
