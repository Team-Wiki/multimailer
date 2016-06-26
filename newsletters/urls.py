from django.conf.urls import url
import newsletters.views

urlpatterns = [
    url(r'^draft/(?P<draft_id>\d+)/$', newsletters.views.PlaintextDraftEditor.as_view(), name="draft_edit"),
]

