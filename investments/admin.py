from django.contrib import admin

from .models import Investment, InvestmentOption, InvestmentReturn


@admin.register(InvestmentOption)
class InvestmentOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'annual_rate', 'funded_from_savings', 'is_active', 'order')
    list_editable = ('annual_rate', 'funded_from_savings', 'is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class InvestmentReturnInline(admin.TabularInline):
    model = InvestmentReturn
    extra = 0


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('member', 'option', 'amount', 'source', 'status', 'created_at')
    list_filter = ('status', 'source', 'option')
    search_fields = ('member__member_id',)
    inlines = [InvestmentReturnInline]


@admin.register(InvestmentReturn)
class InvestmentReturnAdmin(admin.ModelAdmin):
    list_display = ('investment', 'amount', 'created_at', 'recorded_by')
