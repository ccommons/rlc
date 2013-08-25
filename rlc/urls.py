from django.conf.urls import patterns, include, url

# framework admin view class
from django.contrib import admin
admin.autodiscover()

GEN_PREFIX = r'^er'
DOC_PREFIX = GEN_PREFIX + r'/(?P<doc_id>\d+)'
ANNO_PREFIX = DOC_PREFIX + r'/annotation'

A_TYPES = r'/(?P<atype>openq|note|proprev|rev)'
A_ID = r'/(?P<annotation_id>\d+)'
A_BLOCK = r'/(?P<block_id>[a-z0-9-]+)'
A_COMMENT = r'/(?P<comment_id>\d+)'

urlpatterns = patterns('',
    # index page
    url(r'^$', 'er.views.document.index', name='root_index'),
    url(GEN_PREFIX + r'$', 'er.views.document.index', name='index'),

    # main view
    #
    url(DOC_PREFIX + r'$', 'er.views.document.fullpage', name='document_fullview'),

    # annotations

    # previews
    url(ANNO_PREFIX + r'/previews/json$', 'er.views.annotations.preview_json', name='annotation_previews'),

    # general view
    url(ANNO_PREFIX + r'/at' +A_TYPES+ '/json$', 'er.views.annotations.full_json', name='annotation_all'),
    url(ANNO_PREFIX + r'/ai' +A_ID+ '/json$', 'er.views.annotations.full_json', name='annotation_one_of_all'),

    # views in blocks
    url(ANNO_PREFIX + r'/bt' +A_BLOCK+A_TYPES + '/json$', 'er.views.annotations.full_json', name='annotations_in_block'),
    url(ANNO_PREFIX + r'/bi' +A_BLOCK+A_ID + '/json$', 'er.views.annotations.full_json', name='annotation_one_in_block'),

    # annotation compose (no block--for now, manually specify anno type)
    url(ANNO_PREFIX + r'/ct' +A_TYPES+ '/json$', 'er.views.annotations.compose_json', name='annotation_compose'),
    url(ANNO_PREFIX + r'/nt/json$', 'er.views.annotations.add_json', name='annotation_new'),

    # annotation compose (in block)
    url(ANNO_PREFIX + r'/cb' +A_BLOCK+ '/json$', 'er.views.annotations.compose_json', name='annotation_compose_in_block'),
    url(ANNO_PREFIX + r'/nb' +A_BLOCK+'/json$', 'er.views.annotations.add_json', name='annotation_new_in_block'),

    # annotation reply to comment (not in block)
    url(ANNO_PREFIX + r'/arc' +A_COMMENT+ r'/json$', 'er.views.annotations.reply_compose_json', name='annotation_reply'),
    url(ANNO_PREFIX + r'/arn' +A_COMMENT+ r'/json$', 'er.views.annotations.reply_add_json', name='annotation_reply_new'),

    # annotation reply to comment (in block)
    url(ANNO_PREFIX + r'/brc' +A_BLOCK+A_COMMENT+ r'/json$', 'er.views.annotations.reply_compose_json', name='annotation_reply_in_block'),
    url(ANNO_PREFIX + r'/brn' +A_BLOCK+A_COMMENT+ r'/json$', 'er.views.annotations.reply_add_json', name='annotation_reply_new_in_block'),

    # editor
    url(DOC_PREFIX + r'/edit$', 'er.views.edit.formview', name='doc_editor'),
    url(DOC_PREFIX + r'/change$', 'er.views.edit.change', name='doc_change'),

    # notification menu
    url(r'^er/notifications$', 'er.views.notification.notifications_menu', name='notification_menu'),

    # my profile
    url(r'^er/myprofile/json$', 'er.views.profile.profile_json', name='myprofile'),
    # member profile
    url(r'^er/profile/(?P<user_id>\d+)/json$', 'er.views.profile.profile_json', name='profile'),
    # all members
    url(r'^er/members/json$', 'er.views.profile.members_json', name='all_members'),

    # framework administration
    url(r'^admin/', include(admin.site.urls)),

    # framework login
    # note template_name -- not sure if this is a "correct" template, but
    # it seems to work (will need to replace in the product later)
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {"template_name": "admin/login.html"}),

    # Examples:
    # url(r'^$', 'rlc.views.home', name='home'),
    # url(r'^rlc/', include('rlc.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # CKEditor support
    (r'^ckeditor/', include('ckeditor.urls')),

)
