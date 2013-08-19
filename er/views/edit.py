from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from django import forms
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST

from django.core.urlresolvers import reverse

from er.models import EvidenceReview

from document import get_doc

from ckeditor.widgets import CKEditorWidget

import doctags

class EREditForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())
    # XXX add validation stuff
    title = forms.CharField(max_length=100)
    content = forms.CharField(widget=CKEditorWidget())
    # following is for default text widget
    # content = forms.CharField(widget=forms.Textarea())
    publication_link = forms.URLField()
    publication_date = forms.DateTimeField() 

# XXX add editor permission
@login_required
def formview(request, *args, **kwargs):
    """ER editor view"""
    doc = get_doc(**kwargs)
    req_cxt = RequestContext(request)
    data = {
	"content" : doc.content,
	"title" : doc.title,
	"id" : doc.id,
	"publication_link" : doc.publication_link,
	"publication_date" : doc.publication_date,
    }
    form = EREditForm(data)
    context = Context({
    	# "main_document" : content,
	"doctitle" : "Melanoma RLC: Edit " + doc.title,
	"widget_media" : form.media,
	"form" :	form,
	"id" :		doc.id,
    })
    return(render_to_response("edit.html", context, context_instance=req_cxt))


# XXX add editor permission
@login_required
@require_POST
def change(request, *args, **kwargs):
    """ER editor action"""

    form = EREditForm(request.POST)

    if form.is_valid():
    	# any more needed?
	id = form.cleaned_data["id"]
    else:
	# TODO: need better destination
	return HttpResponseRedirect('/er/')

    kwargs = { "doc_id" : id }
    doc = get_doc(**kwargs)
    if doc == None:
	# TODO: need better destination
	return HttpResponseRedirect('/er/')

    parsed_doc = doctags.parse(form.cleaned_data["content"])
    doctags.add_ids(parsed_doc)

    # delete previous section info
    for section in doc.papersection_set.all():
    	section.delete()

    # create new section info
    section_info = doctags.section_info(parsed_doc)
    for section in section_info:
    	doc.papersection_set.create(
	    id=section["id"],
	    header_text=section["text"],
	    position=section["position"],
	)

    doc.content = str(parsed_doc)
    doc.title = form.cleaned_data["title"]
    doc.publication_link = form.cleaned_data["publication_link"]
    doc.publication_date = form.cleaned_data["publication_date"]
    doc.save()

    return HttpResponseRedirect(reverse('document_fullview', kwargs=kwargs))

