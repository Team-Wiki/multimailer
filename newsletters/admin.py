from django.contrib import admin

# Register your models here.
from newsletters.models import PlaintextDraft, Shortlink, Newsletter, Edition, Message, Subscriber, Subscription


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
    list_display = ['edition', 'token', 'target_url',]
    list_filter = ['edition',]
    pass

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'edition', 'enqueued', 'bounced', 'viewed', 'user_agent',]
    list_filter = ['edition',]

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'newsletter', 'state', 'created', 'confirmed']
    list_filter = ['newsletter',]

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['name', 'email_address']
    


