from django.contrib import admin
from models import Author, EvidenceReview, PaperAuthorship
from models import Profile
from models import Annotation, Comment

# ER
admin.site.register(Author)
admin.site.register(EvidenceReview)
admin.site.register(PaperAuthorship)

# profile
admin.site.register(Profile)

# annotations
admin.site.register(Annotation)
admin.site.register(Comment)

