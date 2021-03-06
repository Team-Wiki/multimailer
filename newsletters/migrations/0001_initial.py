# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-27 15:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import newsletters.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Edition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_name', models.CharField(max_length=100)),
                ('mail_subject', models.CharField(max_length=255)),
                ('mail_html_body', models.TextField(blank=True, null=True)),
                ('mail_plain_body', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enqueued', models.DateTimeField(auto_now_add=True)),
                ('bounce_token', models.UUIDField(default=uuid.uuid4)),
                ('bounced', models.DateTimeField(blank=True, null=True)),
                ('bounce_message', models.TextField(blank=True, null=True)),
                ('viewed', models.DateTimeField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('edition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newsletters.Edition')),
            ],
        ),
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('from_name', models.CharField(max_length=50)),
                ('from_email_address', models.EmailField(max_length=50)),
                ('default_plain_template', models.CharField(blank=True, max_length=50, null=True)),
                ('default_html_template', models.CharField(blank=True, max_length=50, null=True)),
                ('plain_footer', models.TextField(blank=True)),
                ('html_footer', models.TextField(blank=True)),
                ('opt_in_subject', models.CharField(max_length=255)),
                ('opt_in_body', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='PlaintextDraft',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_name', models.CharField(max_length=100)),
                ('mail_subject', models.CharField(max_length=255)),
                ('mail_plain_abstract', models.TextField()),
                ('mail_plain_body', models.TextField()),
                ('plain_template', models.CharField(blank=True, max_length=50, null=True)),
                ('html_template', models.CharField(blank=True, max_length=50, null=True)),
                ('newsletter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newsletters.Newsletter')),
            ],
        ),
        migrations.CreateModel(
            name='Shortlink',
            fields=[
                ('token', models.CharField(default=newsletters.models.gen_shortlink_token, max_length=7, primary_key=True, serialize=False, unique=True)),
                ('target_url', models.CharField(max_length=255)),
                ('click_count', models.IntegerField()),
                ('edition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newsletters.Edition')),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=80, null=True)),
                ('email_address', models.EmailField(max_length=254, unique=True)),
                ('state', models.CharField(choices=[('+', 'Active'), ('B', 'Disabled After Bounce'), ('U', 'User Unsubscribed'), ('A', 'Admin Unsubscribed'), ('C', 'Confirmation Pending')], max_length=1)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('confirmed', models.DateTimeField(blank=True, null=True)),
                ('newsletter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newsletters.Newsletter')),
            ],
        ),
        migrations.AddField(
            model_name='message',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newsletters.Subscription'),
        ),
        migrations.AddField(
            model_name='edition',
            name='newsletter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newsletters.Newsletter'),
        ),
        migrations.AlterUniqueTogether(
            name='shortlink',
            unique_together=set([('edition', 'target_url')]),
        ),
    ]
