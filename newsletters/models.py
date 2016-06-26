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
    default_html_template = models.CharField(max_length=50, blank=True, null=True)
    plain_footer = models.TextField(blank=True)
    html_footer = models.TextField(blank=True)

class PlaintextDraft(models.Model):
    newsletter = models.ForeignKey("Newsletter")
    internal_name = models.CharField(max_length=100)
    mail_subject = models.CharField(max_length=255)
    mail_plain_body = models.TextField()
    html_template = models.CharField(max_length=50, blank=True, null=True)

    def build_edition(self):
        ed = Edition()
        ed.newsletter = self.newsletter
        ed.internal_name = self.internal_name
        ed.mail_subject = self.mail_subject
        ed.mail_plain_body = self.mail_plain_body + "\r\n-- \r\n" + self.plain_footer
        if self.html_template:
            ed.mail_html_body = render_to_string(self.html_template, context={
                'newsletter': self.newsletter,
            })
        return ed


class Edition(models.Model):
    newsletter = models.ForeignKey("Newsletter")
    internal_name = models.CharField(max_length=100)
    mail_subject = models.CharField(max_length=255)
    mail_html_body = models.TextField(blank=True,null=True)
    mail_plain_body = models.TextField()

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
        return (txt.replace('*|SUBSCRIBER_ID|*', self.subscription_id)
                   .replace('*|SUBSCRIBER_NAME|*', self.subscription.subscriber.name)
                   .replace('*|SUBSCRIBER_EMAIL|*', self.subscription.subscriber.email_address)
                   .replace('*|MESSAGE_TOKEN|*', self.bounce_token.hex)
                   .replace('*|SUBSCRIBE_DATE|*', self.subscription.confirmed.strftime('%d.%m.%Y'))
                   .replace('*|TODAY|*', datetime.now().strftime('%d.%m.%Y'))
                )

    def get_mime_message(self):
        mPlain = MIMEText(self.preproc_text(self.edition.mail_plain_body), 'plain', 'utf-8')
        if self.edition.mail_html_body == "":
            msg = mPlain
        else:
            mHTML = MIMEText(self.prepare_database_save(self.edition.mail_html_body), 'html', 'utf-8')
            msg = MIMEMultipart('alternative', None, [mPlain, mHTML])
        msg['To'] = email.utils.formataddr((self.subscription.subscriber.name,
                                            self.subscription.subscriber.email_address))
        msg['From'] = email.utils.formataddr((msg.subscription.newsletter.from_name,
                                              msg.subscription.newsletter.from_email_address))
        msg['Subject'] = msg.edition.mail_subject
        msg['List-Unsubscribe'] = reverse('unsubscribe_link', args=(self.bounce_token.hex,))
        msg['List-Help'] = reverse('list_info', args=(self.bounce_token.hex,))
        msg['List-Subscribe'] = reverse('list_info', args=(self.bounce_token.hex,))
        msg['X-Mailer'] = 'MultiMailer'
        msg['Content-Language'] = 'de'

        return msg



