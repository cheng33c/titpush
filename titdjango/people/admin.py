from django.contrib import admin
from .models import PeopleModel

# Register your models here.
class PeopleAdmin(admin.ModelAdmin):
    list_display = ('phone', 'email')
    search_fields = ['phone','email']

admin.site.register(PeopleModel, PeopleAdmin)
