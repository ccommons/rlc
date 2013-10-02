from django.shortcuts import render_to_response
from django.template import Context, RequestContext, Template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from er.models import EvidenceReview, PublicationInfo
from er.models import DefaultDocument
from er.models import Annotation

from django.core.urlresolvers import reverse

from copy import deepcopy

from docutils import get_doc
from annotations import annotation_summary, open_questions_for_main_doc

import re

@login_required
def default(request):
    """redirect to default document or to index"""
    default_docs = DefaultDocument.objects.all()
    if default_docs.count() > 0:
        # redirect to the first default document
        doc_id = default_docs.latest('timestamp').document.id
        url = reverse('document_fullview', kwargs={"doc_id": doc_id})
    else:
        # no default document found; revert to the index
        # redirect to the index
        # (could also call index() here)
        url = reverse('index')

    return(HttpResponseRedirect(url))

@login_required
def index(request):
    """index page"""
    req_cxt = RequestContext(request)
    docs = EvidenceReview.objects.all()

    context = Context({
	"doctitle" : "Melanoma RLC: home",
    	"docs" : docs,
        "tab" : "documents",
    })

    return(render_to_response("index.html", context, context_instance=req_cxt))

@login_required
def fullpage(request, *args, **kwargs):
    """main page view"""
    from er.notification import notification
    notification.mark_read(request)
    req_cxt = RequestContext(request)

    doc = get_doc(**kwargs)

    if doc != None:
    	content = doc.content
    else:
    	content = "no document"

    group_names = [g["name"] for g in request.user.groups.values()]

    sections = doc.papersection_set.order_by('position')

    max_table_label_len = 30
    tables = doc.papertable_set.order_by('position')
    for table in tables:
        table_num = re.sub(r'((Table|TABLE).*\d+)\..*$', r'\1', table.caption)
        table.caption_no_num = re.sub(r'(Table|TABLE).*\d+\.(.*)$', r'\2', table.caption)
        table.label = table_num + ":"
        for word in table.caption_no_num.split():
            if len(table.label + ' ' + word) < max_table_label_len:
                table.label += ' ' + word
            else:
                table.label += ' ...'
                break

    authors = doc.authors.order_by('paperauthorship__position')

    summary = annotation_summary(doc)

    try:
        lpi = PublicationInfo.objects.filter(document=doc).latest('timestamp')
    except PublicationInfo.DoesNotExist:
        lpi = None

    # get URL reverse kwargs for viewing open questions
    oq_kwargs = deepcopy(kwargs)
    oq_kwargs["atype"] = "openq"
    # openq_url = reverse('annotation', kwargs=oq_kwargs)

    # gather all open questions
    # open_questions = Annotation.objects.select_related('doc_block','initial_comment','initial_comment__user').filter(er_doc=doc.id, atype='openq').order_by('doc_block__position', 'timestamp')
    # this actually isn't strictly necessary, because the preview refresh
    # will also put these in, but it's probably helpful to keep the
    # scrollbar from doing weird things after the page loads
    open_questions = open_questions_for_main_doc(doc)

    # TODO: fix this
    from annotations import AnnotationComposeForm
    dummyform = AnnotationComposeForm()
    widget_media = dummyform.media

    # TODO: formalize this
    override_ckeditor = True

    context = {
	"doc" : doc,
        "authors" : authors,
	"doctitle" : "Melanoma RLC: " + doc.title,
        "last_published_info" : lpi,
    	"main_document" : content,
        "open_questions" : open_questions,
        "widget_media" : widget_media,
        "override_ckeditor" : override_ckeditor,
	"group_names" : group_names,
	"sections" : sections,
	"tables" : tables,
        "tab" : "documents",
    }
    context.update(summary)

    return(render_to_response("er.html", context, context_instance=req_cxt))

