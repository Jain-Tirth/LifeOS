# Generated migration for GoogleToken model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0006_alter_emailmessage_user_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField(help_text='Google OAuth access token')),
                ('refresh_token', models.TextField(blank=True, help_text='Google OAuth refresh token', null=True)),
                ('token_uri', models.TextField(help_text='Token endpoint URI (usually https://oauth2.googleapis.com/token)')),
                ('client_id', models.TextField(help_text='OAuth client ID from credentials.json')),
                ('client_secret', models.TextField(help_text='OAuth client secret from credentials.json')),
                ('scopes', models.TextField(help_text='Comma-separated scopes granted')),
                ('expiry', models.DateTimeField(blank=True, help_text='When access_token expires', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='google_token', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Google Tokens',
            },
        ),
        migrations.AddIndex(
            model_name='googletoken',
            index=models.Index(fields=['user'], name='agents_goog_user_id_idx'),
        ),
    ]
