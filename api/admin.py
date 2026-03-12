from django.contrib import admin
from .models import (
    User, Couple, Memory, ImportantDate, Rule, BucketItem, LoveNote,
    LoveLanguage, LoveLanguageAction, GratitudeEntry, DateIdea
)

admin.site.register(User)
admin.site.register(Couple)
admin.site.register(Memory)
admin.site.register(ImportantDate)
admin.site.register(Rule)
admin.site.register(BucketItem)
admin.site.register(LoveNote)

# Phase 1: Advanced Features
admin.site.register(LoveLanguage)
admin.site.register(LoveLanguageAction)
admin.site.register(GratitudeEntry)
admin.site.register(DateIdea)
