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
            if local_parts[0] == 'bounce':
                msg.bounced = datetime.datetime.now()
                msg.bounce_message = peer[0] + "\n" + mailfrom + "\n" + data
                msg.save()
                msg.subscription.state = 'B'
                msg.subscription.save()
                print("OK, handled bounce for "+str(msg.subscription.subscriber))
            elif local_parts[0] == 'unsubscribe':
                msg.subscription.state = 'U'
                msg.subscription.save()
                msg.bounce_message = peer[0] + "\n" + mailfrom + "\n" + data
                msg.save()
                print("OK, handled mail unsubscribe for " + str(msg.subscription.subscriber))
            else:
                print("Ignoring message to "+rcpttos[0])
        except BaseException as ex:
            print("Error while handling bounce")
            print(ex)
        return

server = CustomSMTPServer(('0.0.0.0', 25), None)

asyncore.loop()


