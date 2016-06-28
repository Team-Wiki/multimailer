from django import forms
from newsletters.models import Newsletter, Subscription


class CreateDraftForm(forms.Form):
    newsletter = forms.ModelChoiceField(label='Newsletter', queryset=Newsletter.objects.all())
    internal_name = forms.CharField(label='Interner Titel')

    def __init__(self, session_user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['owner_group'].queryset = Group.objects.filter(user=session_user).order_by('name')


class SubscribeForm(forms.Form):
    name = forms.CharField(label='Ihr Name (optional)', required=False)
    email_address = forms.EmailField(label='Ihre E-Mail-Adresse')


class ChangeSubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['name', 'email_address']


