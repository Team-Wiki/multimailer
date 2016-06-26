from django import forms
from newsletters.models import Newsletter


class CreateDraftForm(forms.Form):
    newsletter = forms.ModelChoiceField(label='Newsletter', queryset=Newsletter.objects.all())
    internal_name = forms.CharField(label='Interner Titel')

    def __init__(self, session_user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['owner_group'].queryset = Group.objects.filter(user=session_user).order_by('name')

