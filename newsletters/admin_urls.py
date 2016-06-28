from django.conf.urls import url
import newsletters.views

urlpatterns = [
    url(r'^draft/new/$', newsletters.views.create_draft, name="draft_create"),
    url(r'^draft/(?P<draft_id>\d+)/$', newsletters.views.PlaintextDraftEditor.as_view(), name="draft_edit"),
    url(r'^edition/(?P<edition_id>\d+)/$', newsletters.views.EditionView.as_view(), name="edition"),
    url(r'^import/(?P<newsletter_id>\d+)/$', newsletters.views.ImportSubscribers.as_view(), name="import_subscribers"),
    url(r'^newsletter/(?P<newsletter_id>\d+)/$', newsletters.views.dashboard, name="newsletter_dashboard"),

]