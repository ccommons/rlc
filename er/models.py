from django.db import models

# get framework user model
from django.contrib.auth.models import User

# ER models
class Author(models.Model):
    author = models.OneToOneField(User, blank=True, null=True)
    author_without_user = models.CharField(max_length=100, blank=True, null=True)

    def name(self):
        if self.author != None:
            return(u"{0} {1}".format(self.author.first_name, self.author.last_name))
        elif self.author_without_user != None:
            return(u"{0}".format(self.author_without_user))
        else:
            return(u"invalid author")

    def __unicode__(self):
        base = self.name()
        if self.author != None:
            base += u" (username: {0})".format(self.author.username)
        elif self.author_without_user != None:
            base += u" (not a user)"
        else:
            base += u" (both fields null)"

        return base

class EvidenceReview(models.Model):
    content = models.TextField()
    title = models.CharField(max_length=100)
    publication_link = models.URLField()
    publication_date = models.DateTimeField()
    revision_date = models.DateTimeField(auto_now=True, auto_now_add=True)

    authors = models.ManyToManyField(Author, through='PaperAuthorship')

    def __unicode__(self):
    	return(self.title)

class DocumentRevision(models.Model):
    paper = models.ForeignKey(EvidenceReview)
    title = models.CharField(max_length=100)
    content = models.TextField()
    revision_date = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
    	return(u"{0}: {1}".format(self.title, self.revision_date.ctime()))

class PaperAuthorship(models.Model):
    author = models.ForeignKey(Author)
    paper = models.ForeignKey(EvidenceReview)
    position = models.IntegerField()

    def __unicode__(self):
    	return(u"{0}: {1} / author num: {2}".format(self.paper.__unicode__(),
                                                    self.author.__unicode__(),
                                                    self.position))

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

# Comment Ratings
class CommentRatingPlus(models.Model):
    comment = models.ForeignKey(Comment, related_name='ratings_plus')
    user = models.ForeignKey(User, related_name='ratings_plus_given')
    rated_user = models.ForeignKey(User, related_name='ratings_plus_received')
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=True)

class CommentRatingMinus(models.Model):
    comment = models.ForeignKey(Comment, related_name='ratings_minus')
    user = models.ForeignKey(User, related_name='ratings_minus_given')
    rated_user = models.ForeignKey(User, related_name='ratings_minus_received')
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=True)

# Annotation

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
        ('comment_annotation', 'Comment'),
        ('comment_news', 'Comment'),
        ('er', 'EvidenceReview'),
        ('user', 'User'),
    }
    etype = models.CharField(max_length=30, choices=EVENT_TYPES)
    ACTIONS = {
        ('new', 'New'),
        ('proprev_accepted', 'Proposed Revision Accepted'),
        ('proprev_rejected', 'Proposed Revision Rejected'),
        ('shared', 'Shared'),
        ('revised', 'Revised'),
        ('updated', 'Updated'),
        ('published', 'Published'),
    }
    action = models.CharField(max_length=20, choices=ACTIONS, null=True)
    # pk of resource table depending on etype, not always integer?
    resource_id = models.CharField(max_length=100)
    # remarks stores additional information of the event
    remarks = models.CharField(max_length=255, default="")

class Notification(models.Model):
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    shown = models.BooleanField(default=False)
    read = models.BooleanField(default=False)

class EmailNotification(models.Model):
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)

# notification preferences here
class EmailPreferences(models.Model):
    user = models.OneToOneField(User)

    activity_note = models.BooleanField(default=True)
    activity_rev = models.BooleanField(default=True)
    activity_openq = models.BooleanField(default=True)
    activity_comment = models.BooleanField(default=True)
    er_revised = models.BooleanField(default=True)
    er_updated = models.BooleanField(default=True)
    er_published = models.BooleanField(default=True)
    new_member = models.BooleanField(default=True)
    shared = models.BooleanField(default=True)

class CommentFollower(models.Model):
    user = models.ForeignKey(User)
    comment = models.ForeignKey(Comment)

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

