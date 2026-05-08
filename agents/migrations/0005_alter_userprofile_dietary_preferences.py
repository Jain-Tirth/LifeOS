# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0004_habits'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='dietary_preferences',
            field=models.JSONField(blank=True, default=dict, help_text="e.g. {'type': 'vegetarian', 'allergies': ['nuts'], 'cuisine': ['Indian', 'Italian']}", null=True),
        ),
    ]
