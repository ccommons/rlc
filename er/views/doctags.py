from bs4 import BeautifulSoup
import uuid
import re

debug = False

def parse(doc_txt):
    doc = BeautifulSoup(doc_txt, "html.parser")
    return(doc)


def find_tables(doc):
    """find tables with captions"""
    table_elements_found = doc.find_all(["table"], recursive=False)
    tables_found = [
        # { "id": .., "position": .., "caption": .., },
    ]
    position = 0
    captions_found = []
    for te in table_elements_found:
        # get id (assume that it has one, possibly added by add_id())
        table_info = { "id": te["id"] }
        tables_found.append(table_info)

        # look for caption
        caption = te.find_previous_sibling("h3", text=re.compile(r"Table.\d+"))
        if caption != []:
            caption_text = caption.get_text()
            if not caption_text in captions_found:
                captions_found.append(caption_text)
            else:
                caption_text = "Caption Not Found"
                caption = None
        else:
            caption_text = "Caption Not Found"
            caption = None

        table_info["caption"] = caption_text
        table_info["position"] = position

        position += 1

    return(tables_found)

def get_tag_info(doc, tag_types):
    """get section information in a document
       you must process doc with add_header_id_attrs() first"""
    position = 0
    tag_info = [] # needs : id, header text, position
    for tag in doc.find_all(tag_types, recursive=False):
	tag_info.append({
	    "id" : tag["id"],
	    "text" : unicode(tag.get_text()),
	    "position" : position,
	})
	position += 1

    return(tag_info)

def section_info(doc):
    return(get_tag_info(doc, ["h1", "h2"]))

def block_info(doc):
    return(get_tag_info(doc, ["div", "p", "table"]))

def add_id_attrs(doc, tag, id_prefix):
    """add id attributes to a document as needed"""

    id_prefix_length = len(id_prefix)
    div_ids = {}

    for tag in doc.find_all(tag, recursive=False):
	gen_id = True

	# look for a pre-existing id attribute
	if tag.has_attr("id"):
	    if tag.attrs["id"] in div_ids:
		# duplicate id; generate a new one
		if debug:
                    print ("duplicate: " + tag.attrs["id"])
		gen_id = True 
	    else: 
		id = tag.attrs["id"]
		if id[:id_prefix_length] == id_prefix:
		    # this id exists and is valid; don't generate a new one
                    if debug:
                        print ("pre-existing: " + id)
		    div_ids[id] = True
		    gen_id = False 
		else:
		    # this id exists, but is invalid; generate a new one
                    if debug:
                        print ("incorrect prefix: " + id)
		    gen_id = True 
	else:
	    # no id at all; generate a new one
            if debug:
                print ("no id:")
	    gen_id = True

	if gen_id:
	    tag["id"] = id_prefix + str(uuid.uuid4())
            if debug:
                print (" > new id:" + tag["id"])

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
    doc = add_id_attrs(doc, "p", "erb-")
    doc = add_id_attrs(doc, "table", "erb-")
    doc = add_id_attrs(doc, "h1", "erh-")
    doc = add_id_attrs(doc, "h2", "erh-")
    return(doc)

# now, need to extract positions of headers in document
# so that we can get the TOC

if __name__ == "__main__":
    debug = True
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

