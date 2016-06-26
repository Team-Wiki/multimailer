from django.core.exceptions import PermissionDenied
from django.http.response import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View
from newsletters.models import PlaintextDraft


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

        return JsonResponse(response)

