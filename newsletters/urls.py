from django.conf.urls import url
import newsletters.views

urlpatterns = [
    url(r'^$', newsletters.views.index_page, name="index"),

    url(r'^list/(?P<newsletter_id>\d+)/', newsletters.views.list_info, name="list_info"),
    url(r'^unsubscribe/(?P<token>\w+)/', newsletters.views.list_unsubscribe, name="list_unsubscribe"),
    url(r'^manage/(?P<token>\w+)/', newsletters.views.list_change_subscription, name="list_change_subscription"),


]

