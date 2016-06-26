from django.contrib import admin

# Register your models here.
from newsletters.models import PlaintextDraft, Shortlink, Newsletter, Edition, Message


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['name']
    pass

@admin.register(PlaintextDraft)
class PlaintextDraftAdmin(admin.ModelAdmin):
    list_display = ['internal_name']
    pass

@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ['internal_name']
    pass

@admin.register(Shortlink)
class ShortlinkAdmin(admin.ModelAdmin):
    pass

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    pass

