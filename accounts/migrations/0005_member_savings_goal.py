from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_member_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='savings_goal',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Optional savings target in KES', max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='member',
            name='savings_goal_label',
            field=models.CharField(blank=True, help_text='What are you saving for? e.g. "Laptop", "School Fees"', max_length=100),
        ),
    ]
