from django.contrib import admin
from models import Author
from models import EvidenceReview, PaperAuthorship, PaperSection, PaperBlock
from models import DocumentRevision
from models import Profile
from models import Annotation, Comment
from models import NewsItem, NewsTag

# ER
admin.site.register(Author)
admin.site.register(EvidenceReview)
admin.site.register(PaperAuthorship)
admin.site.register(PaperSection)
admin.site.register(PaperBlock)

admin.site.register(DocumentRevision)

# profile
admin.site.register(Profile)

# annotations
admin.site.register(Annotation)
admin.site.register(Comment)

# news
admin.site.register(NewsItem)
admin.site.register(NewsTag)

