import uuid
from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.shortcuts import render
from django.template.loader import render_to_string
from newsletters import helper
from django.conf import settings


class Newsletter(models.Model):
    name = models.CharField(max_length=50)
    from_name = models.CharField(max_length=50)
    from_email_address = models.EmailField(max_length=50)
    reply_to_email_address = models.EmailField(max_length=50, blank=True, null=True)
    default_plain_template = models.CharField(max_length=50, blank=True, null=True)
    default_html_template = models.CharField(max_length=50, blank=True, null=True)
    plain_footer = models.TextField(blank=True)
    html_footer = models.TextField(blank=True)

    opt_in_subject = models.CharField(max_length=255)
    opt_in_body = models.TextField()
    #_subject = models.CharField(max_length=255)
    #_body = models.TextField()

    list_info_header = models.TextField()
    list_info_description = models.TextField()

    def __str__(self):
        return self.name

class PlaintextDraft(models.Model):
    newsletter = models.ForeignKey("Newsletter")
    internal_name = models.CharField(max_length=100)
    mail_subject = models.CharField(max_length=255)
    mail_plain_abstract = models.TextField()
    mail_plain_body = models.TextField()
    plain_template = models.CharField(max_length=50, blank=True, null=True)
    html_template = models.CharField(max_length=50, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def build_edition(self):
        ed = Edition()
        ed.newsletter = self.newsletter
        ed.internal_name = self.internal_name
        ed.mail_subject = self.mail_subject

        plain_tpl = 'newsletters/default_plain.txt'
        if self.plain_template: plain_tpl = 'custom_plain/' + self.plain_template + '.txt'

        ed.mail_plain_body = render_to_string(plain_tpl, context={
            'newsletter': self.newsletter,
            'draft': self,
        })

        if self.html_template:
            html_tpl = 'custom_html/' + self.html_template + '.html'
            ed.mail_html_body = render_to_string(html_tpl, context={
                'newsletter': self.newsletter,
                'draft': self,
            })
        return ed
    def __str__(self):
        return self.internal_name + ' (Entwurf) - ' + self.newsletter.name


class Edition(models.Model):
    newsletter = models.ForeignKey("Newsletter")
    internal_name = models.CharField(max_length=100)
    mail_subject = models.CharField(max_length=255)
    mail_html_body = models.TextField(blank=True,null=True)
    mail_plain_body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    display_date = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.internal_name + ' - ' + self.newsletter.name

def gen_shortlink_token():
    return helper.random_token(7)
class Shortlink(models.Model):
    class Meta:
        unique_together = (("edition", "target_url"),)
    token = models.CharField(max_length=7, default=gen_shortlink_token, unique=True, primary_key=True)
    edition = models.ForeignKey("Edition")
    target_url = models.CharField(max_length=255)
    click_count = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)

class Subscription(models.Model):
    class Meta:
        unique_together = ('newsletter', 'email_address')
    SUBSCRIPTION_STATES = (
        ('+', 'Active'),
        ('B', 'Disabled After Bounce'),
        ('U', 'User Unsubscribed'),
        ('A', 'Admin Unsubscribed'),
        ('C', 'Confirmation Pending')
    )
    newsletter = models.ForeignKey("Newsletter")
    name = models.CharField(max_length=80, blank=True, null=True)
    email_address = models.EmailField()
    state = models.CharField(choices=SUBSCRIPTION_STATES, max_length=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    confirmed = models.DateTimeField(blank=True,null=True)
    def build_confirmation_message(self):
        return Message(subscription=self, edition=None, message_type='O')
    def __str__(self):
        return str(self.state) + '  ' + str(self.newsletter) + '  |  ' +  self.name + ' <' + self.email_address + '>'

import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Message(models.Model):
    subscription = models.ForeignKey("Subscription")
    edition = models.ForeignKey("Edition", null=True, blank=True)
    TYPE_CHOICES = (
        ('N', 'Newsletter message'),
        ('O', 'Opt-in confirmation')
    )
    message_type = models.CharField(max_length=1, choices=TYPE_CHOICES, default='N')
    enqueued = models.DateTimeField(auto_now_add=True)
    bounce_token = models.UUIDField(default=uuid.uuid4)
    bounced = models.DateTimeField(blank=True,null=True)
    bounce_message = models.TextField(blank=True,null=True)
    viewed = models.DateTimeField(blank=True,null=True)
    user_agent = models.TextField(blank=True,null=True)

    def preproc_text(self, txt):
        list_info_url = settings.URL_PREFIX + reverse('newsletters:list_info', args=(self.subscription.newsletter_id,))
        list_unsubscribe_url = settings.URL_PREFIX + reverse('newsletters:list_unsubscribe', args=(self.bounce_token.hex,))
        list_change_sub_url = settings.URL_PREFIX + reverse('newsletters:list_change_subscription', args=(self.bounce_token.hex,))
        return (txt.replace('*|SUBSCRIBER_ID|*', str(self.subscription_id))
                   .replace('*|SUBSCRIBER_NAME|*', self.subscription.name)
                   .replace('*|SUBSCRIBER_EMAIL|*', self.subscription.email_address)
                   .replace('*|MESSAGE_TOKEN|*', self.bounce_token.hex)
                   .replace('*|SUBSCRIBE_DATE|*', self.subscription.confirmed.strftime('%d.%m.%Y'))
                   .replace('*|TODAY|*', datetime.now().strftime('%d.%m.%Y'))
                   .replace('*|CHANGE_LINK|*', list_change_sub_url)
                   .replace('*|UNSUBSCRIBE_LINK|*', list_unsubscribe_url)
                )

    def get_message_text(self):
        if self.message_type == 'N':
            return (self.edition.mail_subject, self.edition.mail_plain_body, self.edition.mail_html_body)
        elif self.message_type == 'O':
            s = self.subscription.newsletter.opt_in_body
            s = s.replace('*|CONFIRMATION_LINK|*', settings.URL_PREFIX + reverse('newsletters:confirm_subscription', args=(self.bounce_token,)))
            return (self.subscription.newsletter.opt_in_subject, s, None)

    def get_mime_message(self):
        subject, plain, html = self.get_message_text()
        mPlain = MIMEText(self.preproc_text(plain), 'plain', 'utf-8')
        if self.edition.mail_html_body:
            mHTML = MIMEText(self.preproc_text(html), 'html', 'utf-8')
            msg = MIMEMultipart('alternative', None, [mPlain, mHTML])
        else:
            msg = mPlain
        msg['To'] = email.utils.formataddr((self.subscription.name,
                                            self.subscription.email_address))
        msg['From'] = email.utils.formataddr((self.subscription.newsletter.from_name,
                                              self.subscription.newsletter.from_email_address))
        if self.subscription.newsletter.reply_to_email_address:
            msg['Reply-To'] = self.subscription.newsletter.reply_to_email_address
        msg['Subject'] = subject
        list_info_url = settings.URL_PREFIX + reverse('newsletters:list_info', args=(self.subscription.newsletter_id,))
        list_unsubscribe_url = 'mailto:' + 'unsubscribe-' + self.bounce_token.hex + '@' + settings.BOUNCE_ADDR_HOST
        msg['List-Id'] = msg['From']
        msg['List-Unsubscribe'] = "<"+list_unsubscribe_url+">"
        msg['List-Help'] = "<"+list_info_url+">"
        msg['List-Subscribe'] = "<"+list_info_url+">"
        msg['X-Mailer'] = 'MultiMailer'
        msg['Content-Language'] = 'de'

        return msg



