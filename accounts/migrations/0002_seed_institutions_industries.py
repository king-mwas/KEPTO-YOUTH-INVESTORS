from django.db import migrations

INSTITUTIONS = [
    "University of Nairobi",
    "Kenyatta University",
    "Jomo Kenyatta University of Agriculture and Technology (JKUAT)",
    "Strathmore University",
    "Moi University",
    "Egerton University",
    "Maseno University",
    "Technical University of Kenya",
    "Multimedia University of Kenya",
    "United States International University Africa (USIU-Africa)",
    "Dedan Kimathi University of Technology",
    "Mount Kenya University",
    "Kenya Methodist University",
    "Daystar University",
    "Africa Nazarene University",
    "Kabarak University",
    "Pwani University",
    "South Eastern Kenya University",
    "Masinde Muliro University of Science and Technology",
    "Chuka University",
]

INDUSTRIES = [
    "Technology",
    "Finance & Banking",
    "Agriculture",
    "Healthcare",
    "Education",
    "Retail & Trade",
    "Manufacturing",
    "Hospitality & Tourism",
    "Transport & Logistics",
    "Media & Creative Arts",
    "Construction & Real Estate",
    "Government / Public Service",
    "Other",
]


def seed_data(apps, schema_editor):
    Institution = apps.get_model('accounts', 'Institution')
    Industry = apps.get_model('accounts', 'Industry')

    Institution.objects.bulk_create(
        [Institution(name=name) for name in INSTITUTIONS],
        ignore_conflicts=True,
    )
    Industry.objects.bulk_create(
        [Industry(name=name) for name in INDUSTRIES],
        ignore_conflicts=True,
    )


def remove_data(apps, schema_editor):
    Institution = apps.get_model('accounts', 'Institution')
    Industry = apps.get_model('accounts', 'Industry')
    Institution.objects.filter(name__in=INSTITUTIONS).delete()
    Industry.objects.filter(name__in=INDUSTRIES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, remove_data),
    ]
