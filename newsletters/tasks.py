from __future__ import absolute_import

from celery import shared_task

import smtplib
from newsletters.models import Edition, Message

@shared_task
def deliver_newsletter(edition_id):
    ed = Edition.objects.get(id=edition_id)
    subscriptions = ed.newsletter.subscription_set.filter(state='+')
    for sub in subscriptions:
        msg = Message.objects.create(subscription=sub)
        send_mail.delay(message_id=msg.id)


@shared_task
def send_mail(message_id):
    msg = Message.objects.get(id=message_id)

    server = smtplib.SMTP('127.0.0.1', port=587)
    #server.set_debuglevel(True) # show communication with the server
    mime_message = msg.get_mime_message()
    try:
        server.sendmail('bounce-'+msg.bounce_token.hex+'@bounces.ugbtemp.teamwiki.net',
                        [msg.subscription.subscriber.email_address],
                        mime_message.as_string())
    finally:
        server.quit()