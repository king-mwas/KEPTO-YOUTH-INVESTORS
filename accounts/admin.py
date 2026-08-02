from django.contrib import admin

from .models import Industry, Institution, Member


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        'member_id', 'user', 'phone_number', 'status', 'member_type',
        'institution', 'year_of_study', 'industry', 'business_name', 'created_at',
    ]
    list_display_links = ['member_id']
    list_filter = ['status', 'member_type', 'institution', 'industry']
    search_fields = ['member_id', 'phone_number', 'user__username', 'user__email', 'business_name']
