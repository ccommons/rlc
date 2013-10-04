from django.conf.urls import patterns, include, url

# framework admin view class
from django.contrib import admin
admin.autodiscover()

GEN_PREFIX = r'^er'
DOC_PREFIX = GEN_PREFIX + r'/(?P<doc_id>\d+)'
ANNO_PREFIX = DOC_PREFIX + r'/annotation'
PROFILE_PREFIX = r'^profile'
NOTIFICATION_PREFIX = r'^notifications'

A_TYPES = r'/(?P<atype>openq|note|proprev|rev|acptrev|rejrev)'
A_ID = r'/(?P<annotation_id>\d+)'
A_BLOCK = r'/(?P<block_id>[a-z0-9-]+)'
A_COMMENT = r'/(?P<comment_id>\d+)'
USER_ID = r'/(?P<user_id>\d+)'
RATING_PREFIX = r'^commentrating' + A_COMMENT
FOLLOW_PREFIX = r'^follow' + A_COMMENT
TABLE_PREFIX = DOC_PREFIX + r'/table' + A_BLOCK

urlpatterns = patterns('',
    # index page
    url(r'^$', 'er.views.document.default', name='root'),
    url(GEN_PREFIX + r'$', 'er.views.document.default', name='doc_default'),

    # index
    url(GEN_PREFIX + r'/index/{0,1}$', 'er.views.document.index', name='index'),

    # main view
    #
    url(DOC_PREFIX + r'$', 'er.views.document.fullpage', name='document_fullview'),
    url(DOC_PREFIX + r'/printable$', 'er.views.document.printable', name='document_printable'),

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

    # annotation ratings
    url(RATING_PREFIX + r'/plus/json$', 'er.views.ratings.rate_json', name='rate_plus'),
    url(RATING_PREFIX + r'/minus/json$', 'er.views.ratings.rate_json', name='rate_minus'),

    # editor
    url(DOC_PREFIX + r'/edit$', 'er.views.edit.formview', name='doc_editor'),
    url(DOC_PREFIX + r'/change$', 'er.views.edit.change', name='doc_change'),

    # notification
    url(NOTIFICATION_PREFIX + r'$', 'er.views.notification.notifications_menu', name='notification_menu'),
    url(NOTIFICATION_PREFIX + r'/json$', 'er.views.notification.notifications_json', name='notification_json'),
    url(NOTIFICATION_PREFIX + r'/count/json$', 'er.views.notification.notifications_count_json', name='notification_count_json'),

    # follow
    url(FOLLOW_PREFIX + r'/start/json$', 'er.views.follow.follow_json', name='follow_json'),
    url(FOLLOW_PREFIX + r'/stop/json$', 'er.views.follow.follow_json', name='unfollow_json'),

    # my profile
    url(PROFILE_PREFIX + r'/json$', 'er.views.profile.profile_json', name='myprofile'),
    # member profile
    url(PROFILE_PREFIX + USER_ID + r'/json$', 'er.views.profile.profile_json', name='profile'),
    # all members
    url(PROFILE_PREFIX + r'/all/json$', 'er.views.profile.members_json', name='all_members'),

    # news
    # url(r'^news$', 'er.views.news.index', name='news_index'),

    url(r'^news/json$', 'er.views.news.index_json', {"offset":0}, name='news_index_modal'),
    url(r'^news/o/(?P<offset>\d+)/json$', 'er.views.news.index_json', {"is_addition" : True}, name='news_index_offset_addition'),
    url(r'^news/tag/(?P<tag>.+)/json$', 'er.views.news.index_json', {"offset":0}, name='news_index_tag_modal'),
    url(r'^news/o/(?P<offset>\d+)/tag/(?P<tag>.+)/json$', 'er.views.news.index_json', {"is_addition": True}, name='news_index_tag_offset_addition'),

    url(r'^news/(?P<item_id>\d+)/json$', 'er.views.news.comment_json', name='news_comment'),
    url(r'^news/reply/(?P<comment_id>\d+)/json$', 'er.views.news.reply_json', name='news_reply'),
    url(r'^news/reply/(?P<comment_id>\d+)/new/json$', 'er.views.news.reply_new_json', name='news_reply_new'),

    # tables
    url(TABLE_PREFIX + r'/json$', 'er.views.table.display_json', name='table_modal'),

    # json logged out message
    url(r'^loggedout/json', 'er.views.login.logged_out_json', name='logged_out_json'),

    # framework administration
    url(r'^admin/', include(admin.site.urls)),

    # framework login
    # note template_name -- not sure if this is a "correct" template, but
    # it seems to work (will need to replace in the product later)
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {"template_name": "login/login.html"}, name="login"),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {"next_page":"/"}, name="logout"),

    # Examples:
    # url(r'^$', 'rlc.views.home', name='home'),
    # url(r'^rlc/', include('rlc.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)
