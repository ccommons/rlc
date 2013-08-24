from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required

from django.template.loader import render_to_string
from django.utils import simplejson
from django.http import HttpResponse
from django import forms

from er.models import Profile, EmailPreferences
from er.annotation import comment
from er.profile import conversationItem

class UpdateProfileForm(forms.Form):
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

class UpdateEmailPreferenceForm(forms.Form):
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

@login_required
def profile_json(request, *args, **kwargs):
    req_cxt = RequestContext(request)
    user = request.user
    try:
        profile = user.profile
    except:
        profile = Profile(user=user)

    try:
        email_pref = user.emailpreferences
    except:
        email_pref = EmailPreferences(user=user)

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

    # handle form submission
    if request.method == 'POST':
        profile_form = UpdateProfileForm(request.POST)
        email_form = UpdateEmailPreferenceForm(request.POST)
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

        profile_form = UpdateProfileForm(initial=profile_data)
        email_form = UpdateEmailPreferenceForm(emailpref_data)


    context = Context({
	"modal_id" : modal_id,
        "profile_form" : profile_form,
        "email_form" : email_form,
        "user" : user,
        "profile" : profile,
        "items" : conv_items,
        "num_note" : conv_count.get('note', 0),
        "num_proprev" : conv_count.get('proprev', 0),
        "num_openq" : conv_count.get('openq', 0),
        "num_comment" : conv_count.get('comment', 0),
        "form_action" : request.get_full_path(),
    })

    body_html = render_to_string("myprofile.html", context, context_instance=req_cxt)
    json = simplejson.dumps({
    	"body_html" : body_html,
        "modal_id" : modal_id,
    })

    return(HttpResponse(json, mimetype='application/json'))

