from django.db import models

# get framework user model
from django.contrib.auth.models import User

# ER models
class Author(models.Model):
    author = models.OneToOneField(User, null=True)
    author_without_user = models.CharField(max_length=100, null=True)


class EvidenceReview(models.Model):
    # XXX need to explicitly specify primary key (as string)

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


class PaperSections(models.Model):
    # this will be the uuid in the tag
    id = models.CharField(primary_key=True, max_length=100)
    paper = models.ForeignKey(EvidenceReview)
    header_text = models.CharField(max_length=100)
    position = models.IntegerField()


# Annotation models
class Annotation(models.Model):
    # XXX "context" is a placeholder
    context = models.CharField(max_length=100)
    ANNOTATION_TYPES = {
    	('note', 'Note'),
    	('openq', 'Open Question'),
    	('proprev', 'Proposed Revision'),
    	('rev', 'Revision'),
    }
    atype = models.CharField(max_length=10, choices=ANNOTATION_TYPES, default='note')
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=True)
    # XXX forward into Comment?

class Comment(models.Model):
    # XXX foreign key back to Annotation?
    parent = models.ForeignKey('self', blank=True, null=True, related_name="replies")
    user = models.ForeignKey(User)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=True)

# comment rating -- this is relational. possibly split between negative and
# positive (might speed counts)

# Notification models

# notification preferences here

# News models

# Profile models

# expands basic User class
class Profile(models.Model):
    user = models.OneToOneField(User)

    # there could be multiple titles. well, let's not goldplate this now;
    # it probably has to be dealt with at some point
    title = models.CharField(max_length=100)

    # same with institution
    institution = models.CharField(max_length=100)
    department = models.CharField(max_length=100)

