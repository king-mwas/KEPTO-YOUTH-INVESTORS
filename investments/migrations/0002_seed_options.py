from django.db import migrations


OPTIONS = [
    # name, slug, annual_rate, funded_from_savings, about
    ('Share Capital', 'share-capital', 10, True,
     'Buy into the KEPTO SACCO itself using your savings. Share capital earns '
     'a fixed return per year and makes you a part-owner of the SACCO.'),
    ('Government Bonds', 'government-bonds', None, False,
     'Lend to the Government of Kenya over several years for a set interest rate. '
     'Lower risk, steady returns.'),
    ('Government T-Bills', 'government-t-bills', None, False,
     'Short-term (91/182/364-day) lending to the government. A safe place to park '
     'money for a few months.'),
    ('Kenyan Company Stock / Shares', 'kenyan-stock-shares', None, False,
     'Own shares in listed Kenyan companies on the NSE. Higher risk, and returns '
     'depend on how the companies perform.'),
    ('Liquidity Pool', 'liquidity-pool', None, False,
     'A pooled fund KEPTO members contribute to. Read the About here to see exactly '
     'what the pool is funding — including any group project.'),
    ('Money Market Fund', 'money-market-fund', None, False,
     'A professionally managed fund investing in short-term instruments. Flexible, '
     'with returns that move with the market.'),
]


def seed(apps, schema_editor):
    InvestmentOption = apps.get_model('investments', 'InvestmentOption')
    for i, (name, slug, rate, from_savings, about) in enumerate(OPTIONS):
        InvestmentOption.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name, 'annual_rate': rate, 'funded_from_savings': from_savings,
                'about': about, 'is_active': True, 'order': i,
            },
        )


def unseed(apps, schema_editor):
    InvestmentOption = apps.get_model('investments', 'InvestmentOption')
    InvestmentOption.objects.filter(slug__in=[o[1] for o in OPTIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [('investments', '0001_initial')]
    operations = [migrations.RunPython(seed, unseed)]
