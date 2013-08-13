from er.models import Annotation as mAnnotation
from er.models import Comment as mComment

from django.contrib.auth.models import User

class comment(object):
    """ """
    def __init__(self, *args, **kwargs):
	self.text = None
	self.annotation = None
	self.user = None
	self.timestamp = None
	self.model_object = None
	# self.parent: property
	# self.replies: property

	# create new comment if there are args
	# TODO: clean up argument validation
	if kwargs.has_key("text"):
	    self.model_object = mComment(
		text=kwargs["text"],
		user=User.objects.get(username=kwargs["user"]),
		# annotation=annotation.model_object,
		# user=user,
	    )
	    if kwargs.has_key("annotation"):
	    	# this is a root comment
		annotation = kwargs["annotation"]
		self.model_object.annotation = annotation.model_object

	    self.model_object.save()
	    self.init_from_model()

    def init_from_model(self):
	"""initialize instance data from model"""
	mo = self.model_object
	self.text = mo.text
	self.user = mo.user
	self.timestamp = mo.timestamp
	self.annotation = mo.annotation

    @property
    def replies(self):
    	"""replies to a comment"""
	# TODO: fill this out
	# get IDs of replies

	# instantiate objects
	return []

    @property
    def parent(self):
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
	c.model_object = mComment.objects.get(id=id)
	c.init_from_model()
	return(c)

    def reply(self, *args, **kwargs):
	reply_comment = self.__class__(*args, **kwargs)
	reply_comment.parent = self
	return(reply_comment)

class annotation(object):
    """ """
    def __init__(self, *args, **kwargs):
	self.id = None
	self._index = None
	self._atype = None
	self.comment = None
	self.timestamp = None
	self.model_object = None

	# new annotation
	if kwargs.has_key("comment"):
	    # TODO: validate all arguments

	    # create a new annotation
	    self.model_object = mAnnotation(
		context=kwargs["index"],
		atype=kwargs["atype"],
		# user=user,
	    )

	    self.model_object.save()
	    self.init_from_model()

	    # connect comment
	    c = comment(text=kwargs["comment"],
	                user=kwargs["user"],
			annotation=self)

	    self.comment = c

    @property
    def atype(self):
    	"""annotation type"""
	return self._atype

    @atype.setter
    def atype(self, value):
	# TODO: abstract the following
	valid_types = [at[0] for at in mAnnotation.ANNOTATION_TYPES]
	if value in valid_types:
	    self._atype = value
	else:
	    raise ValueError("annotation type must be one of " + str(valid_types))

    def init_from_model(self):
	"""initialize instance data from model"""
	mo = self.model_object
	self.atype = mo.atype
	self.index = mo.context
	self.timestamp = mo.timestamp
	self.id = mo.id

    @classmethod
    def fetch(annotation, id):
	"""get annotation by index"""
	a = annotation()
	a.model_object = mAnnotation.objects.get(id=id)
	a.init_from_model()
	return(a)

    # XXX necessary?
    def save(self):
	"""save annotation"""
	pass

