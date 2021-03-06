# Generated by Django 2.2.7 on 2020-01-02 11:29

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth2_client', '0002_auto_20191003_1947'),
    ]

    operations = [
        migrations.RenameField(
            model_name='accesstoken',
            old_name='created_at',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='application',
            old_name='created_at',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='application',
            old_name='updated_at',
            new_name='updated',
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='expires',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='raw_token',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, help_text='Token JSON object returned from provider. This is for debugging purposes and can be removed in the future.'),
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='scope',
            field=models.TextField(blank=True, default='', help_text='Scope granted by provider, as a series of space delimited strings, e.g. `read write`', max_length=100),
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='token_type',
            field=models.TextField(default='Bearer', help_text='Token type, most likely Bearer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='application',
            name='authorization_grant_type',
            field=models.CharField(choices=[('client-credentials', 'Client credentials'), ('jwt-bearer', 'JWT bearer')], default='client-credentials', help_text='The type of authorization grant to be used', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='application',
            name='extra_settings',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, help_text="Custom settings JSON string. For data that didn't fit anywhere else"),
        ),
        migrations.RenameField(
            model_name='application',
            old_name='token_url',
            new_name='token_uri',
        ),
        migrations.AlterField(
            model_name='accesstoken',
            name='token',
            field=models.CharField(help_text='The access_token as str', max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='application',
            name='client_id',
            field=models.CharField(help_text='ID string of the application', max_length=100),
        ),
        migrations.AlterField(
            model_name='application',
            name='client_secret',
            field=models.CharField(help_text='Secret string of this application', max_length=255),
        ),
        migrations.AlterField(
            model_name='application',
            name='name',
            field=models.CharField(help_text='Application name', max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='application',
            name='scope',
            field=models.CharField(blank=True, default='', help_text='Scope to be requested from provider, as a series of space delimited strings, e.g. `read write`', max_length=100),
        ),
    ]
