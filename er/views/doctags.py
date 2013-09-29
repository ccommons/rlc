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
        caption = te.find_previous_sibling("h3")
        if caption != [] and caption != None:
            caption_text = caption.get_text()
            if re.search(r"(Table|TABLE).+\d+", caption_text) != None:
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

def process_references(doc):
    """extract references from document"""
    references = {}

    # find the reference info in the references section
    name_re = re.compile(r'^_ENREF_\d+')
    for tag in doc.find_all(["a", "A"], attrs={"name":name_re}, recursive=True):
        ref_name = tag["name"]
        if ref_name in references:
            # TODO: flag error. Reference defined twice.
            pass
        else:
            references[ref_name] = {
                "in_refs": True,
            }

        # get reference text
        text = tag.parent.get_text()
        text = text.replace(u'\xa0', '')
        text = re.sub(r'^\s*\d+\.\s*', '', text)
        text = re.sub(r'\s*http.*$', '', text)

        references[ref_name]["info"] = text

        # look for URL in reference
        parent = tag.parent
        links = parent.find_all(["a", "A"])
        # URL to reference location should be the second one
        if len(links) > 1:
            ref_url = links[1]["href"]
            references[ref_name]["url"] = ref_url

    # find all of the references
    href_re = re.compile(r'^#_ENREF_\d+')
    tags = doc.find_all(["a", "A"], attrs={"href":href_re}, recursive=True)
    for tag in tags:
        ref_name = tag["href"].replace("#", "")
        if ref_name not in references:
            references[ref_name] = {
                "in_refs": False
            }
            # TODO: Flag error. This reference isn't in the refs section.

        if references[ref_name]["in_refs"] == True:
            bib_item = references[ref_name]
            tag["data-ref-info"] = bib_item["info"]

            if "onclick" in tag.attrs:
                del tag["onclick"]

            if "class" not in tag:
                tag["class"] = []

            if "rlc-reference" not in tag["class"]:
                tag["class"].append("rlc-reference")

            if "url" in bib_item:
                tag["url"] = bib_item["url"]

    return(references)

def clean_document(doc):
    """clean up a fresh document"""

    tags_to_unwrap = [
        "font", "FONT",
        "span", "SPAN",
    ]

    # strip out unnecessary/harmful tags
    for tag in doc.find_all(tags_to_unwrap, recursive=True):
        tag.unwrap()

    # remove all classes
    class_re = re.compile(r'.*')
    for tag in doc.find_all(True, attrs={"class":class_re}, recursive=True):
        del tag["class"]

    # hyperlink mess
    hl_re = re.compile(r'file:///.*HYPERLINK')
    for tag in doc.find_all(["a", "A"], attrs={"href":hl_re}, recursive=True):
        href = re.sub(hl_re, u'', tag["href"])
        tag["href"] = href

    # remove all styles
    style_re = re.compile(r'.*')
    for tag in doc.find_all(True, attrs={"style":style_re}, recursive=True):
        del tag["style"]

    # remove empty paragraphs
    for tag in doc.find_all(['p', 'P'], recursive=False):
        text = tag.get_text()
        if (len(text) < 5):
            if re.search(r'^\s+$', text, flags=re.UNICODE) != None:
                tag.decompose()

def get_tag_info(doc, tag_types):
    """get section information in a document
       you must process doc with add_header_id_attrs() first"""
    position = 0
    tag_info = [] # needs : id, header text, position
    for tag in doc.find_all(tag_types, recursive=False):
        text = unicode(tag.get_text())
        if text.strip() == "":
            continue
	tag_info.append({
	    "id" : tag["id"],
	    "text" : text,
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

