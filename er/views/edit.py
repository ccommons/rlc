from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from django import forms
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST

from django.core.urlresolvers import reverse

from er.models import EvidenceReview, PaperSection, PaperBlock

from docutils import get_doc

# from ckeditor.widgets import CKEditorWidget

import doctags

class EREditForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())
    title = forms.CharField(max_length=100)
    # content = forms.CharField(widget=CKEditorWidget())
    # following is for default text widget
    content = forms.CharField(widget=forms.Textarea())
    publication_link = forms.URLField()
    publication_date = forms.DateTimeField() 

# TODO: add editor permission
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
	"form" : form,
	"id" : doc.id,
        "tab" : "documents",
        "override_ckeditor" : True,
    })
    return(render_to_response("edit.html", context, context_instance=req_cxt))


# TODO: add editor permission
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

    # update sections

    # get old section info
    old_section_values = doc.papersection_set.values("id", "tag_id", "position", "header_text")
    old_ids = set([old_section["tag_id"] for old_section in old_section_values])
    old_section_info = {}
    for s in old_section_values:
        old_section_info[s["tag_id"]] = s

    # extract new section info
    new_section_info = doctags.section_info(parsed_doc)
    new_ids = set([section["id"] for section in new_section_info])

    unchanged_ids = old_ids.intersection(new_ids)
    added_ids = new_ids.difference(old_ids)
    deleted_ids = old_ids.difference(new_ids)

    for section in new_section_info:
        id = section["id"]
        if id in added_ids:
            doc.papersection_set.create(
                tag_id=id,
                header_text=section["text"],
                position=0,
                # position=section["position"],
            )
        else:
            # update if necessary
            old_section = old_section_info[id]
            if (old_section["header_text"] != section["text"]):
                # positions are too slow
                # or old_section["position"] != section["position"]:
                # TODO: possibly get all of the changed sections at once,
                # update them all at once
                try:
                    s = doc.papersection_set.get(tag_id=id)
                    s.header_text = section["text"]
                    # s.position = section["position"]
                    s.save()
                except:
                    # TODO: get rid of all, create new section
                    pass

    # delete removed sections
    for section in doc.papersection_set.filter(tag_id__in=deleted_ids):
        section.delete()

    # update blocks

    # get old block info
    old_block_values = doc.paperblock_set.values("id", "tag_id", "position", "preview_text")
    old_ids = set([old_block["tag_id"] for old_block in old_block_values])
    old_block_info = {}
    for b in old_block_values:
        old_block_info[b["tag_id"]] = b

    # extract new block info
    new_block_info = doctags.block_info(parsed_doc)
    new_ids = set([block["id"] for block in new_block_info])

    unchanged_ids = old_ids.intersection(new_ids)
    added_ids = new_ids.difference(old_ids)
    deleted_ids = old_ids.difference(new_ids)

    # add / update blocks
    for block in new_block_info:
        id = block["id"]
        preview_text = block["text"][:100]
        if id in added_ids: # new block
            doc.paperblock_set.create(
                tag_id=id,
                preview_text=preview_text,
                position=0,
                # positions are too slow
                # position=block["position"],
            )
        else: # existing block; update if necessary
            old_block = old_block_info[id]
            if old_block["preview_text"] != preview_text:
                # updating positions causes slow chain-reactions
                # or old_block["position"] != block["position"]):
                try:
                    b = doc.paperblock_set.get(tag_id=id)
                    b.preview_text = preview_text
                    # b.position = block["position"]
                    # positions are too slow
                    b.save()
                except:
                    # TODO: multiple blocks: get rid of all, create new block
                    pass

    # delete removed blocks
    for block in doc.paperblock_set.filter(tag_id__in=deleted_ids):
        block.delete()

    doc.content = str(parsed_doc)
    doc.title = form.cleaned_data["title"]
    doc.publication_link = form.cleaned_data["publication_link"]
    doc.publication_date = form.cleaned_data["publication_date"]
    doc.save()

    return HttpResponseRedirect(reverse('document_fullview', kwargs=kwargs))

