from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lib.main.models import *

class OrganizationAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('users', 'admins', 'projects')

class InventoryAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')

# FIXME: Add the rest of the models...

admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Inventory, InventoryAdmin)
