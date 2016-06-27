from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http.response import JsonResponse, HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View
from newsletters import tasks
from newsletters.forms import CreateDraftForm, ChangeSubscriptionForm
from newsletters.models import PlaintextDraft, Edition, Subscription, Message, Newsletter


@login_required
def create_draft(request):
    if request.method == 'POST':
        form = CreateDraftForm(session_user=request.user, data=request.POST)
        if form.is_valid():
            cb = PlaintextDraft(newsletter = form.cleaned_data['newsletter'],
                                internal_name= form.cleaned_data['internal_name'])

            cb.save()

            return HttpResponseRedirect(reverse('newsletters:draft_edit', args=[cb.id]))
    else:
        form = CreateDraftForm(session_user=request.user)

    return render(request, 'newsletters/draft_create.html', {'form': form})



def list_unsubscribe(request, token):
    tok = UUID(token)
    msg = Message.objects.get(bounce_token=tok)
    subscription = msg.subscription
    if request.method == 'POST':
        subscription.state = 'U'
        subscription.save()
        return render(request, 'newsletters/unsubscribe_ack.html', {'newsletter': subscription.newsletter})
    else:
        return render(request, 'newsletters/unsubscribe_form.html', {'subscription': subscription, 'token': msg.bounce_token.hex})

def list_change_subscription(request, token):
    tok = UUID(token)
    msg = Message.objects.get(bounce_token=tok)
    subscription = msg.subscription

    saved = False
    if request.method == 'POST':
        form = ChangeSubscriptionForm(instance=subscription.subscriber, data=request.POST)
        if form.is_valid():
            form.save()
            saved = True
    else:
        form = ChangeSubscriptionForm(instance=subscription.subscriber)

    return render(request, 'newsletters/change_subscription.html', {'form': form,
                                                                    'token': msg.bounce_token.hex,
                                                                    'saved': saved})


def list_info(request, id):
    nl = Newsletter.objects.get(id=id)
    return render(request, 'newsletters/list_info.html', {'newsletter': nl})


class PlaintextDraftEditor(View):
    def get(self, request, draft_id, *args, **kwargs):
        if not request.user.has_perm('newsletters.change_plaintextdraft'): raise PermissionDenied
        draft = PlaintextDraft.objects.get(id=draft_id)
        return render(request, "newsletters/draft_editor.html",
                      {'draft': draft, 'newsletter': draft.newsletter})

    def post(self, request, draft_id, *args, **kwargs):
        if not request.user.has_perm('newsletters.change_plaintextdraft'): raise PermissionDenied
        draft = PlaintextDraft.objects.get(id=draft_id)

        response = {}

        if 'save' in request.POST:
            if 'mail_subject' in request.POST: draft.mail_subject = request.POST['mail_subject']
            if 'mail_plain_body' in request.POST: draft.mail_plain_body = request.POST['mail_plain_body']
            if 'html_template' in request.POST: draft.html_template = request.POST['html_template']
            draft.save()
            response['success'] = True

        if 'preview' in request.POST:
            ed = draft.build_edition()
            response['success'] = True
            response['preview_html'] = ed.mail_html_body

        if 'create_edition' in request.POST:
            ed = draft.build_edition()
            ed.save()
            response['success'] = True
            response['edition_id'] = ed.id
            response['edition_url'] = reverse('newsletters:edition', args=[ed.id])

        return JsonResponse(response)



class EditionView(View):
    def get(self, request, edition_id, *args, **kwargs):
        if not request.user.has_perm('newsletters.change_plaintextdraft'): raise PermissionDenied
        edition = Edition.objects.get(id=edition_id)
        return render(request, "newsletters/edition_view.html",
                      {'edition': edition, })

    def post(self, request, edition_id, *args, **kwargs):
        if not request.user.has_perm('newsletters.change_plaintextdraft'): raise PermissionDenied
        edition = Edition.objects.get(id=edition_id)

        response = {}

        if 'start_sending' in request.POST:
            tasks.deliver_newsletter.delay(edition.id)
            response['success'] = True

        return JsonResponse(response)

