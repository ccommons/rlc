from er.models import EvidenceReview

def get_doc(**kwargs):
    """return a document object in accordance to the url param spec"""
    if "doc_id" in kwargs:
    	doc_id = int(kwargs["doc_id"])
    else:
    	doc_id = -1

    try:
	doc = EvidenceReview.objects.get(id=doc_id)
    except:
    	doc = None
	# XXX should raise or redirect here to something sane

    return(doc)

