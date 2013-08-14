from django.contrib import admin
from models import Author, EvidenceReview, PaperAuthorship, PaperSection
from models import Profile
from models import Annotation, Comment

# ER
admin.site.register(Author)
admin.site.register(EvidenceReview)
admin.site.register(PaperAuthorship)
admin.site.register(PaperSection)

# profile
admin.site.register(Profile)

# annotations
admin.site.register(Annotation)
admin.site.register(Comment)

