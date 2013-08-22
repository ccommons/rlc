from django.conf.urls import patterns, include, url

# framework admin view class
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # index page
    url(r'^$', 'er.views.document.index', name='root_index'),
    url(r'^er/$', 'er.views.document.index', name='index'),

    # main view
    #
    # url(r'^er/$', 'er.views.document.fullpage', name='mainview'),
    #
    url(r'^er/(?P<doc_id>\d+)$', 'er.views.document.fullpage', name='document_fullview'),

    # annotations

    # previews
    url(r'^er/(?P<doc_id>\d+)/annotation/previews/json$', 'er.views.annotations.preview_json', name='annotation_previews'),

    # general view
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<atype>openq)/json$', 'er.views.annotations.full_json', name='annotation'),
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<atype>openq)/(?P<annotation_id>\d+)/json$', 'er.views.annotations.full_json', name='annotation_one_of_all'),

    # views in blocks
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<block_id>[a-z0-9-]+)/(?P<atype>openq|note|proprev|rev)/json$', 'er.views.annotations.full_json', name='annotations_in_block'),
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<block_id>[a-z0-9-]+)/(?P<atype>openq|note|proprev|rev)/(?P<annotation_id>\d+)/json$', 'er.views.annotations.full_json', name='annotation_one_in_block'),

    # annotation compose (no block)
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<atype>openq)/compose/json$', 'er.views.annotations.compose_json', name='annotation_compose'),
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<atype>openq)/new/json$', 'er.views.annotations.add_json', name='annotation_new'),

    # annotation compose (in block)
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<block_id>[a-z0-9-]+)/any/compose/json$', 'er.views.annotations.compose_json', name='annotation_compose_in_block'),
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<block_id>[a-z0-9-]+)/any/new/json$', 'er.views.annotations.add_json', name='annotation_new_in_block'),

    # annotation reply to comment
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<atype>openq|note|proprev|rev)/(?P<annotation_id>\d+)/(?P<comment_id>\d+)/reply/json$', 'er.views.annotations.reply_json', name='annotation_reply'),
    url(r'^er/(?P<doc_id>\d+)/annotation/(?P<atype>openq|note|proprev|rev)/(?P<annotation_id>\d+)/(?P<comment_id>\d+)/reply/new/json$', 'er.views.annotations.reply_add_json', name='annotation_reply_new'),

    # TODO: reply to comment in block

    # editor
    url(r'^er/(?P<doc_id>\d+)/edit$', 'er.views.edit.formview', name='doc_editor'),
    url(r'^er/(?P<doc_id>\d+)/change$', 'er.views.edit.change', name='doc_change'),


    # notification menu
    url(r'^er/notifications$', 'er.views.notification.notifications_menu', name='notification_menu'),

    # profile
    url(r'^er/myprofile/json$', 'er.views.profile.profile_json', name='myprofile'),


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
