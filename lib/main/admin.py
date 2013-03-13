from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lib.main.models import *

class OrganizationAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')

admin.site.register(Organization, OrganizationAdmin)
