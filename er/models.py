from django.db import models

# get framework user model
from django.contrib.auth.models import User

# ER models
class Author(models.Model):
    author = models.OneToOneField(User, null=True)
    author_without_user = models.CharField(max_length=100, null=True)


class EvidenceReview(models.Model):
    # TODO(?): explicitly specify primary key (as string)?

    content = models.TextField()
    title = models.CharField(max_length=100)
    publication_link = models.URLField()
    publication_date = models.DateTimeField()
    revision_date = models.DateTimeField(auto_now=True, auto_now_add=True)

    authors = models.ManyToManyField(Author, through='PaperAuthorship')

    def __unicode__(self):
    	return(self.title)


class PaperAuthorship(models.Model):
    author = models.ForeignKey(Author)
    paper = models.ForeignKey(EvidenceReview)
    position = models.IntegerField()


class PaperSection(models.Model):
    # this will be the uuid in the tag
    id = models.CharField(primary_key=True, max_length=100)
    paper = models.ForeignKey(EvidenceReview)
    header_text = models.CharField(max_length=100)
    position = models.IntegerField()


# Annotation models
class Comment(models.Model):
    # parent is null if this is the root comment
    parent = models.ForeignKey('self', blank=True, null=True, related_name="replies")

    user = models.ForeignKey(User)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
    	return('id: {0} / user: {1} / "{2}"'.format(self.id, self.user.username, self.text))

# comment rating -- this is relational. possibly split between negative and
# positive (might speed counts)
# (comment rating model(s) go here)

class DiscussionPoint(models.Model):
    # abstract base class for annotations and news comments
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=True)
    initial_comment = models.OneToOneField(Comment)

    class Meta:
	abstract = True

class Annotation(DiscussionPoint):
    context = models.CharField(max_length=100)
    ANNOTATION_TYPES = {
    	('note', 'Note'),
    	('openq', 'Open Question'),
    	('proprev', 'Proposed Revision'),
    	('rev', 'Revision'),
    }
    atype = models.CharField(max_length=10, choices=ANNOTATION_TYPES, default='note')

    def __unicode__(self):
    	return("Annotation id: {0} / ct: {1}".format(self.id, self.context))


# TODO: investigate if subclassing works with this
# class AnnotationInER(models.Model):
#     annotation = models.OneToOneField(Annotation)
#     # need both ER doc and er section because er section can be null
#     er_doc = models.ForeignKey(EvidenceReview, related_name="annotation_locations")
#     er_section = models.ForeignKey(PaperSection, blank=True, null=True, on_delete=models.SET_NULL, related_name="annotation_locations")

# News Item Annotation Index (place this below)

# Notification models

# Notification preferences here

# News models

# Profile models

# Expands basic User class
class Profile(models.Model):
    user = models.OneToOneField(User)

    # there could be multiple titles. well, let's not goldplate this now;
    # it probably has to be dealt with at some point
    title = models.CharField(max_length=100)

    # same with institution
    institution = models.CharField(max_length=100)
    department = models.CharField(max_length=100)

