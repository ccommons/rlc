from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse
from django import forms
from django.core.urlresolvers import reverse

from er.models import Profile
#from er.models import Comment, Annotation
from er.annotation import comment

from datetime import datetime

class UpdateProfileForm(forms.Form):
    title = forms.CharField(required=False, max_length=100)
    department = forms.CharField(required=False, max_length=100)
    institution = forms.CharField(required=False, max_length=100)
    email = forms.EmailField(required=False)
    new_password = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="New password (again)", widget=forms.PasswordInput)

class conversationItem(object):
    """Transform data for presentation"""

    CTYPE_MAP = {
        'openq' : 'Open Question',
        'proprev' : 'Proposed Revision',
        'rev' : 'Revision',
        'note' : 'Note',
    }

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
                        atype=self._atype,
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
        self._ctype = self.__class__.CTYPE_MAP.get(ctype, ctype)
    
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

@login_required
def profile_json(request, *args, **kwargs):
    req_cxt = RequestContext(request)
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
    except:
        profile = Profile(user=user)

    comments = comment.fetch_by_user(user)

    conv_count = {'comment':0}
    conv_items = []
    for c in comments:
        try:
            # TODO: incorporate into comment class
            a = c.root.model_object.annotation
            conv_item = conversationItem(c.model_object.id, doc_id=a.er_doc.id, atype=a.atype, annotation_id=a.id)
            if c.is_root():
                # an annotation
                if a.atype in conv_count:
                    conv_count[a.atype] += 1
                else:
                    conv_count[a.atype] = 1
                conv_item.ctype = a.atype
                if a.doc_block:
                    conv_item.context = a.doc_block.preview_text
                else:
                    conv_item.context = c.text[:100]
                conv_item.comments = len(c.thread_as_list()) - 1
            else:
                # a reply
                conv_count['comment'] += 1
                conv_item.ctype = 'comment'
                conv_item.context = c.text[:100]
                # does not count comments for replies
        except:
            continue
        else:
            conv_item.timestamp = c.timestamp
            conv_items.append(conv_item)

    modal_id = "modal_id_myprofile"
    profile_data = {
        "title" : profile.title,
        "department" : profile.department,
        "institution" : profile.institution,
        "email" : user.email,
    }
    form = UpdateProfileForm(initial=profile_data)
    context = Context({
	"modal_id" : modal_id,
        "form" : form,
        "user" : user,
        "profile" : profile,
        "items" : conv_items,
        "num_note" : conv_count.get('note', 0),
        "num_proprev" : conv_count.get('proprev', 0),
        "num_openq" : conv_count.get('openq', 0),
        "num_comment" : conv_count.get('comment', 0),
    })

    body_html = render_to_string("myprofile.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
        "modal_id" : modal_id,
    })

    return(HttpResponse(json, mimetype='application/json'))

