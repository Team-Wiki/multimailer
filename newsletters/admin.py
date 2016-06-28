from django.contrib import admin

# Register your models here.
from newsletters.models import PlaintextDraft, Shortlink, Newsletter, Edition, Message, Subscription


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
    list_display = ['newsletter_name', 'edition_name', 'subscriber_str', 'enqueued', 'bounced', 'viewed', 'user_agent',]
    list_display_links = ['newsletter_name', 'edition_name', 'subscriber_str',]
    list_filter = ['edition',]
    def newsletter_name(self, obj):
        return obj.edition.newsletter.name
    newsletter_name.short_description = "Newsletter"
    def edition_name(self, obj):
        return obj.edition.internal_name
    edition_name.short_description = "Ausgabe"
    def subscriber_str(self, obj):
        return obj.subscription.email_address
    subscriber_str.short_description = "Abonnent"

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'email_address', 'newsletter', 'state', 'created', 'confirmed']
    list_filter = ['newsletter',]



