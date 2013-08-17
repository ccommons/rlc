from django.conf.urls import patterns, include, url

# framework admin view class
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # index page
    url(r'^$', 'er.views.document.index', name='index'),
    url(r'^er/$', 'er.views.document.index', name='index'),

    # main view
    #
    # url(r'^er/$', 'er.views.document.fullpage', name='mainview'),
    #
    url(r'^er/(?P<er_id>\d+)$', 'er.views.document.fullpage', name='mainview'),

    # annotation
    # TODO: add specific annotation
    url(r'^er/(?P<er_id>\d+)/annotation/(?P<atype>openq)/json$', 'er.views.document.annotation_json', name='annotation'),

    # editor
    url(r'^er/(?P<er_id>\d+)/edit$', 'er.views.edit.formview', name='ereditor'),
    url(r'^er/(?P<er_id>\d+)/change$', 'er.views.edit.change', name='erchange'),

    # get all annotations
    # url(r'^er/XXX/notes/', 'er.views.document.fullpage', name='mainview'),
    # view one annotation
    # url(r'^er/XXX/notes/ARGS$', 'er.views.document.fullpage', name='mainview'),


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
