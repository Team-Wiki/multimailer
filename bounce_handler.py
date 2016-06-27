#!/usr/bin/env python3
from uuid import UUID

import datetime

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "multimailer.settings")
import django
django.setup()

from newsletters.models import Message, Subscription



import smtpd

import asyncore

class ModifiedHeloSMTPChannel(smtpd.SMTPChannel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fqdn = "bounces.ugbtemp.teamwiki.net"


class CustomSMTPServer(smtpd.SMTPServer):
    channel_class = ModifiedHeloSMTPChannel
    def process_message(self, peer, mailfrom, rcpttos, data):
        print ('Receiving message from:', peer)
        print ('Message addressed from:', mailfrom)
        print ('Message addressed to  :', rcpttos)
        print ('Message length        :', len(data))
        try:
            rcpt_addr = rcpttos[0].split('@')
            print(rcpt_addr)
            local_parts = rcpt_addr[0].split('-')
            guid = UUID(local_parts[1])
            msg = Message.objects.get(bounce_token=guid)
            msg.bounced = datetime.datetime.now()
            msg.bounce_message = peer + "\n" + mailfrom + "\n" + data
            msg.save()
            msg.subscription.state = 'B'
            msg.subscription.save()
            print("OK, unsubscribed "+str(msg.subscription.subscriber))
        except BaseException as ex:
            print("Error while handling bounce")
            print(ex)
        return

server = CustomSMTPServer(('0.0.0.0', 25), None)

asyncore.loop()


