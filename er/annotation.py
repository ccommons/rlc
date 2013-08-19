from er.models import Comment as mComment
from er.models import Annotation as mAnnotation

from django.contrib.auth.models import User

class comment(object):
    """Represents an annotation comment"""
   
    def __config__(self):
	self.CommentModel = mComment

    def __init__(self, *args, **kwargs):
	self.text = None	# can be made into property
	self.user = None
	self.timestamp = None
	self.model_object = None
	# self.parent: property
	# self.replies: property

	self.__config__()

	# create new comment if there are args
	# TODO: clean up argument validation
	if "text" in kwargs:
	    self.model_object = self.CommentModel(
		text=kwargs["text"],
		user=User.objects.get(username=kwargs["user"]),
	    )

	    self.model_object.save()
	    self.init_from_model()

    def init_from_model(self):
	"""initialize instance data from model"""
	mo = self.model_object
	self.text = mo.text
	self.user = mo.user
	self.timestamp = mo.timestamp

    @property
    def replies(self):
    	"""get all replies to a comment"""
	reply_ids = [r.id for r in self.model_object.replies.order_by('timestamp')]
	replies = [self.__class__.fetch(id) for id in reply_ids]
	return replies

    @property
    def parent(self):
	"""get parent comment, if any"""
	parent_obj = self.model_object.parent
	if parent_obj != None:
	    return self.__class__.fetch(parent_obj.id)
	else:
	    return None

    @parent.setter
    def parent(self, parent_comment):
	self.model_object.parent = parent_comment.model_object
	self.model_object.save()

    @classmethod
    def fetch(comment, id):
	"""get comment by index"""
	c = comment()
	c.model_object = c.CommentModel.objects.get(id=id)
	c.init_from_model()
	return(c)

    def reply(self, *args, **kwargs):
	reply_comment = self.__class__(*args, **kwargs)
	reply_comment.parent = self
	return(reply_comment)

    def thread_as_list(self):
	"""return the comment thread as a list, in threaded order"""
	comment_stack = [([self], 0)]
	output = []
	while comment_stack != []:
	    (comments, level) = comment_stack[-1]
	    if comments == []:
		# nothing left in the current level to process
	    	comment_stack.pop()
	    else:
		# process next comment in current level
		next_comment = comments.pop(0)
		next_comment.level = level
		output.append(next_comment)
		replies = next_comment.replies
		if replies != []:
		    # if there are replies to this comment, add them to the
		    # list of comments to process at a new level
		    comment_stack.append((replies, level + 1))

	return(output)

class discussionpoint(object):
    """Discussion point abstract base class"""
    def __config__(self):
	"""initializer for subclasses"""
	self.Model = None

    def model_config(self, model_kwargs, orig_kwargs):
	"""model configuration (fill in for subclasses)"""
	pass

    def __init__(self, *args, **kwargs):
	self.id = None
	self.comment = None
	self.timestamp = None
	self.model_object = None

	self.__config__()

	# new annotation
	if "comment" in kwargs:
	    # TODO: validate all arguments

	    c = comment(text=kwargs["comment"],
	                user=kwargs["user"])

	    self.comment = c

	    mod_kwargs = {
		"initial_comment" : c.model_object,
	    }

	    # subclass-specific model configuration
	    self.model_config(mod_kwargs, kwargs)

	    # create a new model
	    self.model_object = self.Model(**mod_kwargs)
	    self.model_object.save()

	    self.init_from_model_super()

    def init_from_model_super(self):
	"""initialize instance data from model"""
	mo = self.model_object
	self.timestamp = mo.timestamp
	self.id = mo.id
	self.comment = comment.fetch(mo.initial_comment.id)
	self.init_from_model()

    def init_from_model(self):
	"""fill in for subclasses"""
	pass

    @classmethod
    def fetch(this_class, id):
	"""get a discussion point by ID"""
	a = this_class()
	a.model_object = a.Model.objects.get(id=id)
	a.init_from_model_super()
	return(a)

class annotation(discussionpoint):
    """Annotation for RLC document"""
    def __config__(self):
	self._index = None
	self._atype = None
	self.Model = mAnnotation

    def model_config(self, model_kwargs, orig_kwargs):
	model_kwargs["context"] = orig_kwargs["index"]
	model_kwargs["atype"] = orig_kwargs["atype"]

    def init_from_model(self):
	mo = self.model_object
	self._atype = mo.atype
	self.index = mo.context

    @property
    def atype(self):
    	"""annotation type"""
	return self._atype

    @atype.setter
    def atype(self, value):
	# TODO: abstract the following
	valid_types = [at[0] for at in self.Model.ANNOTATION_TYPES]
	if value in valid_types:
	    self._atype = value
	    self.model_object.atype = value
	    self.model_object.save()
	else:
	    raise ValueError("annotation type must be one of " + str(valid_types))

    @property
    def document(self):
    	"""annotation type"""
	return self.model_object.er_doc

    @document.setter
    def document(self, value):
        self.model_object.er_doc = value
        self.model_object.save()

    @classmethod
    def doc_all(this_class, doc):
	"""get all annotations from a document"""
        # TODO: filters (types, sections)
        return([this_class.fetch(a.id) for a in doc.annotations.all()])

