from django.contrib import admin

# Register your models here.
from newsletters.models import PlaintextDraft, Shortlink, Newsletter, Edition, Message


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    pass

@admin.register(PlaintextDraft)
class PlaintextDraftAdmin(admin.ModelAdmin):
    pass

@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    pass

@admin.register(Shortlink)
class ShortlinkAdmin(admin.ModelAdmin):
    pass

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    pass

