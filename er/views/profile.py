from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from er.login_decorators import login_required_json
from django.contrib.auth.models import User

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse
from django import forms
from operator import itemgetter

from er.models import Profile, EmailPreferences
from er.annotation import comment
from er.profile import conversationItem

from ratings import attach_ratings

class updateProfileForm(forms.Form):
    title = forms.CharField(required=False, max_length=100)
    department = forms.CharField(required=False, max_length=100)
    institution = forms.CharField(required=False, max_length=100)
    email = forms.EmailField(required=False)
    new_password = forms.CharField(required=False, widget=forms.PasswordInput)
    new_password2 = forms.CharField(required=False, label="New password (again)", widget=forms.PasswordInput)

    def clean(self):
        password = self.cleaned_data.get('new_password')
        password2 = self.cleaned_data.get('new_password2')
        if password != password2:
            # can't target specific field in current version or django
            # the error is put in self.non_field_errors
            # workaround is not using .as_p(), print non_field_errors before password field
            raise forms.ValidationError("Passwords don't match")
        return self.cleaned_data

class updateEmailPreferenceForm(forms.Form):
    all_notifications = forms.BooleanField(required=False)
    activity_all = forms.BooleanField(required=False)
    activity_note = forms.BooleanField(required=False)
    activity_rev = forms.BooleanField(required=False)
    activity_openq = forms.BooleanField(required=False)
    activity_comment = forms.BooleanField(required=False)
    er_all = forms.BooleanField(required=False)
    er_revised = forms.BooleanField(required=False)
    er_updated = forms.BooleanField(required=False)
    er_published = forms.BooleanField(required=False)
    new_members = forms.BooleanField(required=False)


@login_required_json
def profile_json(request, *args, **kwargs):
    modal_id = "modal_profile"
    req_cxt = RequestContext(request)
    this_url_name = request.resolver_match.url_name
    if this_url_name == 'myprofile':
        myprofile = True
    else:
        myprofile = False

    calling_user = request.user

    if myprofile:
        user = request.user
    else:
        try:
            user = User.objects.get(id=kwargs.get('user_id', 0))
        except:
            json = simplejson.dumps({
                "body_html" : 'User not found',
                "modal_id" : modal_id,
            })

            return(HttpResponse(json, mimetype='application/json'))

    try:
        profile = user.profile
    except:
        profile = Profile(user=user)

    if myprofile:
        try:
            email_pref = user.emailpreferences
        except:
            email_pref = EmailPreferences(user=user)

    comments = comment.fetch_by_user(user, max=20)

    attach_ratings(comments, user=calling_user)

    conv_items = []
    for c in comments:
        try:
            # TODO: incorporate into comment class
            a = c.root.model_object.annotation

            conv_item = conversationItem(c.model_object.id, doc_id=a.er_doc.id, atype=a.atype, annotation_id=a.id)

            # needed for rating
            conv_item.comment = c

            if c.is_root():
                # an annotation
                conv_item.ctype = a.atype

                # I believe we just show the comment, not the context
                conv_item.context = c.text[:100]

                # if a.doc_block:
                #     conv_item.context = a.doc_block.preview_text
                # else:
                #     conv_item.context = c.text[:100]

                # conv_item.comments = len(c.thread_as_list()) - 1
                # this is too slow, revert to model object

                conv_item.comments = c.model_object.replies.count()

            else:
                # a reply
                conv_item.ctype = 'comment'
                conv_item.context = c.text[:100]
                # does not count comments for replies
        except:
            pass
        else:
            conv_item.timestamp = c.timestamp
            conv_items.append(conv_item)
            continue

        # news comment
        try:
            n = c.root.model_object.newsitem
            conv_item = conversationItem(c.model_object.id, item_id=n.id)
            # needed for rating
            conv_item.comment = c
            conv_item.ctype = 'comment'
            conv_item.context = c.text[:100]
            conv_item.timestamp = c.timestamp
            conv_items.append(conv_item)
        except:
            pass

    if myprofile:
        # handle form submission
        if request.method == 'POST':
            profile_form = updateProfileForm(request.POST)
            email_form = updateEmailPreferenceForm(request.POST)
            if profile_form.is_valid() and email_form.is_valid():
                # save
                cd = profile_form.cleaned_data
                profile.title = cd['title']
                profile.department = cd['department']
                profile.institution = cd['institution']
                profile.save()
                if cd['new_password']:
                    user.set_password(cd['new_password'])
                user.email = cd['email']
                user.save()
                cd = email_form.cleaned_data

                email_pref.activity_note = cd['activity_note']
                email_pref.activity_rev = cd['activity_rev']
                email_pref.activity_openq = cd['activity_openq']
                email_pref.activity_comment = cd['activity_comment']
                email_pref.er_revised = cd['er_revised']
                email_pref.er_updated = cd['er_updated']
                email_pref.er_published = cd['er_published']
                email_pref.new_member = cd['new_members']

                if cd['activity_all']:
                    email_pref.activity_note = True
                    email_pref.activity_rev = True
                    email_pref.activity_openq = True
                    email_pref.activity_comment = True

                if cd['er_all']:
                    email_pref.er_revised = True
                    email_pref.er_updated = True
                    email_pref.er_published = True

                if cd['all_notifications']:
                    email_pref.activity_note = True
                    email_pref.activity_rev = True
                    email_pref.activity_openq = True
                    email_pref.activity_comment = True
                    email_pref.er_revised = True
                    email_pref.er_updated = True
                    email_pref.er_published = True
                    email_pref.new_member = True
                email_pref.save()
        else:
            activity_all = email_pref.activity_note and email_pref.activity_rev and email_pref.activity_openq and email_pref.activity_comment
            er_all = email_pref.er_revised and email_pref.er_updated and email_pref.er_published
            all_notifications = activity_all and er_all and email_pref.new_member

            emailpref_data = {
                'all_notifications' : all_notifications,
                'activity_all' : activity_all,
                'activity_note' : email_pref.activity_note,
                'activity_rev' : email_pref.activity_rev,
                'activity_openq' : email_pref.activity_openq,
                'activity_comment' : email_pref.activity_comment,
                'er_all' : er_all,
                'er_revised' : email_pref.er_revised,
                'er_updated' : email_pref.er_updated,
                'er_published' : email_pref.er_published,
                'new_members' : email_pref.new_member,
            }

            profile_data = {
                "title" : profile.title,
                "department" : profile.department,
                "institution" : profile.institution,
                "email" : user.email,
            }

            profile_form = updateProfileForm(initial=profile_data)
            email_form = updateEmailPreferenceForm(emailpref_data)



    conv_summary = user_summary(user)

    context = Context({
	"modal_id" : modal_id,
        "user" : user,
        "profile" : profile,
        "items" : conv_items,
        "num_note" : conv_summary["count"]["note"],
        "num_proprev" : conv_summary["count"]["proprev"],
        "num_openq" : conv_summary["count"]["openq"],
        "num_comment" : conv_summary["count"]["comment"],
    })

    if myprofile:
        context['profile_form'] = profile_form
        context['email_form'] = email_form
        context['form_action'] = request.get_full_path()

    body_html = render_to_string("myprofile.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
        "modal_id" : modal_id,
    })

    return(HttpResponse(json, mimetype='application/json'))


# TODO: maybe want to move this into ../annotation.py
from er.models import Comment
from django.db.models import Count

def user_summary(user):
    """get a summary of annotations and comments for a user"""
    anno_summary = user.comment_set.values('annotation__atype').annotate(num_annotations=Count('annotation__id'))
    num_comments = user.comment_set.exclude(parent__isnull=True).count()

    m = {
        'count' : {
            'comment' : num_comments,
            'openq' : 0,
            'note' : 0,
            'proprev' : 0,
        },
        'contribution' : 0,
    }

    for a in anno_summary:
        atype = a["annotation__atype"]
        if atype != None:
            m["count"][atype] = a["num_annotations"]
            m["contribution"] += a["num_annotations"]

    return m


class membersSortForm(forms.Form):
    SORT_ORDER_CHOICES = (('contribution', 'Top Contributors',), ('firstname', 'Alphabetical'),)
    sort_order = forms.ChoiceField(widget=forms.RadioSelect, choices=SORT_ORDER_CHOICES)

@login_required_json
def members_json(request, *args, **kwargs):
    req_cxt = RequestContext(request)
    modal_id = "modal_members"

    initial_values = {'sort_order':'contribution',}
    sort_order = initial_values['sort_order']

    if request.method == 'POST':
        form = membersSortForm(request.POST)
        form.is_valid()
        sort_order = form.cleaned_data.get('sort_order', sort_order)
    else:
        form = membersSortForm(initial=initial_values)

    users = User.objects.exclude(username="news").order_by('first_name', 'last_name')

    members = []
    for user in users:
        try:
            profile = user.profile
        except:
            profile = Profile(user=user)

        m = user_summary(user)
        m["user"] = user
        m["profile"] = profile

        members.append(m)

    if sort_order == 'contribution':
        members = sorted(members, key=itemgetter('contribution'), reverse=True)

    context = Context({
	"modal_id" : modal_id,
        "members" : members,
        "form" : form,
        "form_action" : request.get_full_path(),
    })

    body_html = render_to_string("members.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
        "modal_id" : modal_id,
    })

    return(HttpResponse(json, mimetype='application/json'))
