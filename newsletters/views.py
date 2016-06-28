import csv
from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.db.utils import IntegrityError
from django.http.response import JsonResponse, HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View
from newsletters import tasks
from newsletters.forms import CreateDraftForm, ChangeSubscriptionForm, SubscribeForm
from newsletters.models import PlaintextDraft, Edition, Subscription, Message, Newsletter

def newsletter_menu_cp(request):
    if request.user and request.user.is_staff:
        return {
            'all_newsletters': Newsletter.objects.all()
        }
    else:
        return {}

@login_required
def create_draft(request):
    if request.method == 'POST':
        form = CreateDraftForm(session_user=request.user, data=request.POST)
        if form.is_valid():
            nl = form.cleaned_data['newsletter']
            cb = PlaintextDraft.objects.create(newsletter = nl,
                                 internal_name=form.cleaned_data['internal_name'],
                                 mail_subject=form.cleaned_data['internal_name'],
                                 plain_template=nl.default_plain_template,
                                 html_template=nl.default_html_template,
                                )
            return HttpResponseRedirect(reverse('nleditor:draft_edit', args=[cb.id]))
    else:
        initial = {}
        if 'newsletter_id' in request.GET: initial['newsletter'] = Newsletter.objects.get(id=request.GET['newsletter_id'])
        form = CreateDraftForm(session_user=request.user, initial=initial)


    return render(request, 'newsletters/draft_create.html', {'form': form})



def index_page(request):
    newsletters = Newsletter.objects.all()
    return render(request, 'newsletters/index.html', {'newsletters': newsletters})


def dashboard(request, newsletter_id):
    nl = Newsletter.objects.get(id=newsletter_id)
    drafts = nl.plaintextdraft_set.order_by('-created')
    editions = nl.edition_set.order_by('-created')

    return render(request, 'newsletters/dashboard.html', {
        'newsletter': nl,
        'drafts': drafts,
        'editions': editions,
        'active_subscriber_count': nl.subscription_set.filter(state='+').count(),
        'bounced_subscriber_count': nl.subscription_set.filter(state='B').count(),
        'unsubscribed_subscriber_count': nl.subscription_set.filter(Q(state='U')|Q(state='A')).count(),
        'pending_subscriber_count': nl.subscription_set.filter(Q(state='C')).count(),
        'subscribe_url': settings.URL_PREFIX+reverse('newsletters:list_info', args=(nl.id,)),
    })


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
        form = ChangeSubscriptionForm(instance=subscription, data=request.POST)
        if form.is_valid():
            form.save()
            saved = True
    else:
        form = ChangeSubscriptionForm(instance=subscription)

    return render(request, 'newsletters/change_subscription.html', {'form': form,
                                                                    'token': msg.bounce_token.hex,
                                                                    'saved': saved})


def subscribe_to_newsletter(name, email_address, nl):
    s, created = Subscription.objects.get_or_create(email_address=email_address,
                                newsletter=nl, defaults={'name': name, 'state': 'C',})
    if not created:
        if s.state == '+':
            raise Exception('Sie haben den Newsletter bereits abonniert.')
        else:
            s.state = 'C'
            s.save()
    return True



def list_info(request, newsletter_id):
    nl = Newsletter.objects.get(id=newsletter_id)

    if request.method == 'POST':
        form = SubscribeForm(data=request.POST)
        if form.is_valid():
            try:
                subscribe_to_newsletter(form.cleaned_data['email_address'], form.cleaned_data['email_address'], nl)
                return render(request, 'newsletters/subscribe_optin_message.html', {'newsletter': nl})
            except Exception as ex:
                return render(request, 'newsletters/message.html',
                              {'newsletter': nl, 'result': str(ex)})
    else:
        form = SubscribeForm()

    return render(request, 'newsletters/list_info.html', {'newsletter': nl, 'subscribe_form': form})


class ImportSubscribers(View):
    def get(self, request, newsletter_id, *args, **kwargs):
        if not request.user.has_perm('newsletters.add_subscription'): raise PermissionDenied
        foo = ""
        return render(request, "newsletters/import_view.html",
                      {'title': 'Abonnenten importieren', 'output': ''})

    def post(self, request, newsletter_id, *args, **kwargs):
        if not request.user.has_perm('newsletters.add_subscription'): raise PermissionDenied

        nl = Newsletter.objects.get(id=newsletter_id)

        the_csv = request.POST["content"]
        reader = csv.reader(the_csv.splitlines(), delimiter='\t')

        out = ""
        for line in reader:
            if len(line) < 5: continue
            out += '<li>Email "' + line[3] + '" ...'
            try:
                s, created = Subscription.objects.get_or_create(email_address=line[3],
                                                              newsletter=nl,
                                            defaults={'name': line[4], 'confirmed': datetime.now() })
                s.state = '+'
                s.save()
                out += "ok"
            except IntegrityError as ex:
                out += str(ex)

        return render(request, "newsletters/import_view.html", {'title': 'Erfolg', 'output': out})


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
            if 'mail_plain_abstract' in request.POST: draft.mail_plain_abstract = request.POST['mail_plain_abstract']
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
            response['edition_url'] = reverse('nleditor:edition', args=[ed.id])

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

