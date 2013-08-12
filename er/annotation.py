from er.models import Annotation as mAnnotation
from er.models import Comment as mComment

class comment(object):
    """ """
    def __init__(self):
	pass

    def reply(self):	# XXX needs comment class?
    	pass

class annotation(object):
    """ """
    def __init__(self):
	self._index = None
	self._atype = None
	self._comments = None
	self._timestamp = None
	self.model_object = None

    @property
    def comments(self):
    	"""comments in annotation"""
	return self._comments

    # discard this later; comments will have their own interface
    @comments.setter
    def comments(self, value):
	self._comments = value

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
	    # TODO: fill in "something"
	    raise something

    @classmethod
    def new(self, index, atype, user, comment):
	"""new annotation"""

    @classmethod
    def fetch(self, index):
	"""get annotation by index"""
	nanno = self()
	nanno.model_object = mAnnotation.objects.get(context=index)
	mo = nanno.model_object
	nanno.atype = mo.atype
	nanno.timestamp = mo.timestamp
	return(nanno)

    # XXX necessary?
    def save(self):
	"""save annotation"""
	pass

