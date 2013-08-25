from django.core.urlresolvers import reverse
from er.views.annotations import atype_to_name
from datetime import datetime

class conversationItem(object):
    """Transform data for presentation"""

    def __init__(self, id, **kwargs):
        self._id = id
        self._ctype = ""
        self._age = ""
        self._url = ""
        self._context = ""
        self._ratings = 0
        self._comments = 0

        self._timestamp = None
        self._now = datetime.utcnow()

        # for generating url
        self._doc_id = kwargs.get('doc_id', '')
        self._atype = kwargs.get('atype', '')
        self._annotation_id = kwargs.get('annotation_id', '')
    
    @property
    def url(self):
        if not self._url:
            if self._doc_id and self._atype and self._annotation_id:
                url_kwargs = dict(
                        doc_id=self._doc_id,
                        annotation_id=self._annotation_id)
                self._url = reverse('annotation_one_of_all', kwargs=url_kwargs)
        return self._url

    @property
    def id(self):
        return self._id

    @property
    def ctype(self):
        return self._ctype
    @ctype.setter
    def ctype(self, ctype):
        self._ctype = atype_to_name(ctype) or ctype
    
    @property
    def context(self):
        return self._context
    @context.setter
    def context(self, context):
        self._context = context
    
    @property
    def comments(self):
        return self._comments
    @comments.setter
    def comments(self, comments):
        self._comments = comments

    @property
    def timestamp(self):
        return self._timestamp
    @timestamp.setter
    def timestamp(self, timestamp):
        if self._timestamp:
            raise Exception("timestamp has been set before")
        timestamp = timestamp.replace(tzinfo=None)
        self._timestamp = timestamp
        # set age
        timedelta = self._now - timestamp
        daysdiff = self._now.day - timestamp.day
        if timedelta.days <2:
            if not daysdiff:
                # hour/minute
                hours = int(timedelta.seconds)/3600
                if hours < 1:
                    minutes = int(timedelta.seconds)/60
                    display = '%d minute%s ago' % (minutes, '' if minutes == 1 else 's')
                else:
                    display = '%d hour%s ago' % (hours, '' if hours == 1 else 's')
            elif daysdiff == 1:
                display = "yesterday"
            else:
                display = "2 days ago"
        else:
            display = '%s days ago' % daysdiff
        self._age = display

    @property
    def age(self):
        return self._age

