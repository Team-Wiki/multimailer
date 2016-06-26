import uuid
from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.shortcuts import render
from django.template.loader import render_to_string
from newsletters import helper


class Newsletter(models.Model):
    name = models.CharField(max_length=50)
    from_name = models.CharField(max_length=50)
    from_email_address = models.EmailField(max_length=50)
    default_plain_template = models.CharField(max_length=50, blank=True, null=True)
    default_html_template = models.CharField(max_length=50, blank=True, null=True)
    plain_footer = models.TextField(blank=True)
    html_footer = models.TextField(blank=True)
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

class Subscriber(models.Model):
    name = models.CharField(max_length=80)
    email_address = models.EmailField()
    def __str__(self):
        return self.name + ' <' + self.email_address + '>'

class Subscription(models.Model):
    SUBSCRIPTION_STATES = (
        ('+', 'Active'),
        ('B', 'Disabled After Bounce'),
        ('U', 'User Unsubscribed'),
        ('A', 'Admin Unsubscribed'),
        ('C', 'Confirmation Pending')
    )
    newsletter = models.ForeignKey("Newsletter")
    subscriber = models.ForeignKey("Subscriber")
    state = models.CharField(choices=SUBSCRIPTION_STATES, max_length=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    confirmed = models.DateTimeField(blank=True,null=True)

import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Message(models.Model):
    subscription = models.ForeignKey("Subscription")
    edition = models.ForeignKey("Edition")
    enqueued = models.DateTimeField(auto_now_add=True)
    bounce_token = models.UUIDField(default=uuid.uuid4)
    bounced = models.DateTimeField(blank=True,null=True)
    bounce_message = models.TextField(blank=True,null=True)
    viewed = models.DateTimeField(blank=True,null=True)
    user_agent = models.TextField(blank=True,null=True)

    def preproc_text(self, txt):
        return (txt.replace('*|SUBSCRIBER_ID|*', str(self.subscription_id))
                   .replace('*|SUBSCRIBER_NAME|*', self.subscription.subscriber.name)
                   .replace('*|SUBSCRIBER_EMAIL|*', self.subscription.subscriber.email_address)
                   .replace('*|MESSAGE_TOKEN|*', self.bounce_token.hex)
                   .replace('*|SUBSCRIBE_DATE|*', self.subscription.confirmed.strftime('%d.%m.%Y'))
                   .replace('*|TODAY|*', datetime.now().strftime('%d.%m.%Y'))
                )

    def get_mime_message(self):
        mPlain = MIMEText(self.preproc_text(self.edition.mail_plain_body), 'plain', 'utf-8')
        if self.edition.mail_html_body:
            mHTML = MIMEText(self.preproc_text(self.edition.mail_html_body), 'html', 'utf-8')
            msg = MIMEMultipart('alternative', None, [mPlain, mHTML])
        else:
            msg = mPlain
        msg['To'] = email.utils.formataddr((self.subscription.subscriber.name,
                                            self.subscription.subscriber.email_address))
        msg['From'] = email.utils.formataddr((self.subscription.newsletter.from_name,
                                              self.subscription.newsletter.from_email_address))
        msg['Subject'] = self.edition.mail_subject
        msg['List-Unsubscribe'] = reverse('newsletters:list_unsubscribe', args=(self.bounce_token.hex,))
        msg['List-Help'] = reverse('newsletters:list_info', args=(self.bounce_token.hex,))
        msg['List-Subscribe'] = reverse('newsletters:list_info', args=(self.bounce_token.hex,))
        msg['X-Mailer'] = 'MultiMailer'
        msg['Content-Language'] = 'de'

        return msg



