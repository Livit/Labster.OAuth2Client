# Generated by Django 2.1.7 on 2019-03-12 09:58

import django_extensions.db.fields.json
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', django_extensions.db.fields.json.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Example: licence', max_length=50)),
                ('client_id', models.CharField(max_length=100)),
                ('client_secret', models.CharField(max_length=255)),
                ('service_host', models.CharField(help_text='Service host. For example: http://service-a:8000 or https://serive-a.labster.com', max_length=200)),
                ('token_url', models.CharField(help_text='Token URL. For example: http://service-a:8000/o/token/', max_length=200)),
                ('scope', models.CharField(blank=True, default='', help_text='Custom permissions string. Empty value is allowed, and set by default.', max_length=100)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='application',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='oauth2_client.Application'),
        ),
    ]
