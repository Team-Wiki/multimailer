from django.conf.urls import url
import newsletters.views

urlpatterns = [
    url(r'^draft/new/$', newsletters.views.create_draft, name="draft_create"),
    url(r'^draft/(?P<draft_id>\d+)/$', newsletters.views.PlaintextDraftEditor.as_view(), name="draft_edit"),
    url(r'^edition/(?P<edition_id>\d+)/$', newsletters.views.EditionView.as_view(), name="edition"),
    url(r'^import/(?P<newsletter_id>\d+)/$', newsletters.views.ImportSubscribers.as_view(), name="import_subscribers"),

    url(r'^list/(?P<newsletter_id>\d+)/', newsletters.views.list_info, name="list_info"),
    url(r'^unsubscribe/(?P<token>\w+)/', newsletters.views.list_unsubscribe, name="list_unsubscribe"),
    url(r'^manage/(?P<token>\w+)/', newsletters.views.list_change_subscription, name="list_change_subscription"),


]

