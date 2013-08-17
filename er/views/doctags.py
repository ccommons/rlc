from bs4 import BeautifulSoup
import uuid

def parse(doc_txt):
    doc = BeautifulSoup(doc_txt, "html.parser")
    return(doc)

def section_info(doc):
    """get section information in a document
       you must process doc with add_header_id_attrs() first"""
    position = 0
    tag_info = [] # needs : id, header text, position
    for tag in doc.find_all(["h1", "h2"]):
	tag_info.append({
	    "id" : tag["id"],
	    "text" : unicode(tag.string),
	    "position" : position,
	})
	position += 1

    return(tag_info)

def add_id_attrs(doc, tag, id_prefix):
    """add id attributes to a document as needed"""

    id_prefix_length = len(id_prefix)
    div_ids = {}

    for tag in doc.find_all(tag):
	gen_id = True

	# look for a pre-existing id attribute
	if tag.has_attr("id"):
	    if tag.attrs["id"] in div_ids:
		# duplicate id; generate a new one
		# print ("duplicate: " + tag.attrs["id"])
		gen_id = True 
	    else: 
		id = tag.attrs["id"]
		if id[:id_prefix_length] == id_prefix:
		    # this id exists and is valid; don't generate a new one
		    # print ("pre-existing: " + id)
		    div_ids[id] = True
		    gen_id = False 
		else:
		    # this id exists, but is invalid; generate a new one
		    # print ("incorrect prefix: " + id)
		    gen_id = True 
	else:
	    # no id at all; generate a new one
	    # print ("no id")
	    gen_id = True

	if gen_id:
	    tag["id"] = id_prefix + str(uuid.uuid4())

    # not really necessary, because doc is mutable and has been changed
    return(doc)

def add_div_id_attrs(doc):
    doc = add_id_attrs(doc, "div", "erb-")
    return(doc)

def add_header_id_attrs(doc):
    doc = add_id_attrs(doc, "h1", "erh-")
    return(doc)

def add_ids(doc):
    doc = add_id_attrs(doc, "div", "erb-")
    doc = add_id_attrs(doc, "h1", "erh-")
    doc = add_id_attrs(doc, "h2", "erh-")
    return(doc)

# now, need to extract positions of headers in document
# so that we can get the TOC

if __name__ == "__main__":
    testdoc = """<h1>sec1</h1><div>here is some stuff</div>
    <div id="erb-exists">this one has an id already</div>
    <div id="erb-exists">this one reuses, needs new one</div>
    <div id="wrong-prefix">this one reuses, needs new one</div>
    <div>here is some more stuff</div>
    <h1>this is another section</h1>
    <div>a block in the second section</div>
    """
    doc = parse(testdoc)
    add_div_id_attrs(doc)
    add_header_id_attrs(doc)
    print(doc)
    print section_info(doc)

