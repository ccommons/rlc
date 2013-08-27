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
    # id = models.CharField(primary_key=True, max_length=100)
    # this will be the uuid in the tag
    tag_id = models.CharField(max_length=100)
    paper = models.ForeignKey(EvidenceReview)
    header_text = models.CharField(max_length=100)
    position = models.IntegerField()

    def __unicode__(self):
    	return(u"{0} / {1}".format(self.tag_id, self.header_text[:20]))

class PaperBlock(models.Model):
    # id = models.CharField(primary_key=True, max_length=100)
    # this will be the uuid in the tag
    tag_id = models.CharField(max_length=100)
    paper = models.ForeignKey(EvidenceReview)
    preview_text = models.CharField(max_length=100)
    position = models.IntegerField()

    def __unicode__(self):
    	return(u"{0} / {1}".format(self.tag_id, self.preview_text[:40]))

# Annotation models
class Comment(models.Model):
    # parent is null if this is the root comment
    parent = models.ForeignKey('self', blank=True, null=True, related_name="replies")
    root = models.ForeignKey('self', blank=True, null=True, related_name="all_replies")

    user = models.ForeignKey(User)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
    	return(u'id: {0} / user: {1} / "{2}"'.format(self.id, self.user.username, self.text[:120]))

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
    ANNOTATION_TYPES = [
    	('note', 'Note'),
    	('openq', 'Open Question'),
    	('proprev', 'Proposed Revision'),
    	('rev', 'Revision'),
    ]
    atype = models.CharField(max_length=10, choices=ANNOTATION_TYPES, default='note')
    # TODO: remove null from the following (easier to debug when null allowed)
    er_doc = models.ForeignKey(EvidenceReview, related_name="annotations", null=True)
    doc_block = models.ForeignKey(PaperBlock, blank=True, null=True, on_delete=models.SET_NULL, related_name="annotations")

    def __unicode__(self):
    	return(u"Annotation id: {0} / ct: {1}".format(self.id, self.context))


# TODO: investigate if subclassing works with this
# class AnnotationInER(models.Model):
#     annotation = models.OneToOneField(Annotation)
#     # need both ER doc and er section because er section can be null
#     er_doc = models.ForeignKey(EvidenceReview, related_name="annotation_locations")
#     er_section = models.ForeignKey(PaperSection, blank=True, null=True, on_delete=models.SET_NULL, related_name="annotation_locations")

# News Item Annotation Index (place this below)

# Notification models
class Event(models.Model):
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    EVENT_TYPES = {
        ('annotation', 'Annotation'),
        ('comment', 'Comment'),
        ('er', 'EvidenceReview'),
        ('user', 'User'),
    }
    etype = models.CharField(max_length=15, choices=EVENT_TYPES)
    ACTIONS = {
        ('new', 'New'),
        ('revised', 'Revised'),
        ('updated', 'Updated'),
        ('published', 'Published'),
    }
    action = models.CharField(max_length=10, choices=ACTIONS, null=True)
    # pk of resource table depending on etype, not always integer?
    resource_id = models.CharField(max_length=100)
    # remarks stores additional information of the event
    # e.g. the root of the comment for a comment type event
    # root of comment stored in format type:pk. E.g. 'annotation:12', 'news:7'.
    # reason not to use json is that this simple string is easier for grouping
    remarks = models.CharField(max_length=255, default="")

class Notification(models.Model):
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    shown = models.BooleanField(default=False)
    read = models.BooleanField(default=False)

# notification preferences here
class EmailPreferences(models.Model):
    user = models.OneToOneField(User)

    activity_note = models.BooleanField()
    activity_rev = models.BooleanField()
    activity_openq = models.BooleanField()
    activity_comment = models.BooleanField()
    er_revised = models.BooleanField()
    er_updated = models.BooleanField()
    er_published = models.BooleanField()
    new_member = models.BooleanField()

# News models
class NewsItem(models.Model):
    # For Melanoma RLC, this will always be "melanoma"
    site = models.CharField(max_length=30, default="melanoma")
    url = models.CharField(max_length=250)
    title = models.CharField(max_length=500)
    preview = models.TextField()
    comments = models.OneToOneField(Comment)
    pubdate = models.DateTimeField(auto_now=False, auto_now_add=True)

    # for use in templates
    def tag_objects(self):
        return(self.tags.all())

    def __unicode__(self):
    	return(u"News Item: {0}".format(self.title[:30]))

class NewsTag(models.Model):
    news_items = models.ManyToManyField(NewsItem, related_name="tags")
    tag_value = models.CharField(max_length=30)

    def __unicode__(self):
    	return(u"News tag: {0}".format(self.tag_value))

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

