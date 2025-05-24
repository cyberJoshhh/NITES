from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import SchoolYear

@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'is_active', 'start_date', 'end_date', 'status', 'generate_next_year_button')
    list_filter = ('is_active',)
    search_fields = ('year',)
    readonly_fields = ('created_at', 'updated_at')

    def status(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    status.short_description = 'Status'

    def generate_next_year_button(self, obj):
        if obj.is_expired:
            return format_html(
                '<a class="button" href="{}">Generate Next School Year</a>',
                f'generate-next-year/{obj.id}/'
            )
        return "Not expired"
    generate_next_year_button.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'generate-next-year/<int:school_year_id>/',
                self.admin_site.admin_view(self.generate_next_year),
                name='generate-next-year',
            ),
        ]
        return custom_urls + urls

    def generate_next_year(self, request, school_year_id):
        school_year = SchoolYear.objects.get(id=school_year_id)
        new_school_year, message = school_year.generate_next_school_year()
        
        if new_school_year:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
        return HttpResponseRedirect("../")
