from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_member_savings_goal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='savings_goal',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Optional savings target in KES (any amount)', max_digits=15, null=True),
        ),
    ]
