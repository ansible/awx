import json
from django import forms
from django.utils.translation import ugettext_lazy as _
from jsonfield.fields import JSONFormField
from lib.main.models import *

class HostAdminForm(forms.ModelForm):

    class Meta:
        model = Host
    
    vdata = JSONFormField(label=_('Variable data'), required=False, widget=forms.Textarea(attrs={'class': 'vLargeTextField'}))

    def __init__(self, *args, **kwargs):
        super(HostAdminForm, self).__init__(*args, **kwargs)
        if self.instance.variable_data:
            print repr(self.instance.variable_data.data)
            self.initial['vdata'] = self.instance.variable_data.data

    def save(self, commit=True):
        instance = super(HostAdminForm, self).save(commit=commit)
        save_m2m = getattr(self, 'save_m2m', lambda: None)
        vdata = self.cleaned_data.get('vdata', '')
        print 'vdata', repr(vdata)
        def new_save_m2m():
            save_m2m()
            if not instance.variable_data:
                instance.variable_data = VariableData.objects.create(data=vdata)
                instance.save()
            else:
                variable_data = instance.variable_data
                # FIXME!!!
                #variable_data.data = vdata
                #variable_data.save()
        if commit:
            new_save_m2m()
        else:
            self.save_m2m = new_save_m2m
        return instance

class GroupForm(forms.ModelForm):

    class Meta:
        model = Host

    variable_data = JSONFormField(required=False, widget=forms.Textarea(attrs={'class': 'vLargeTextField'}))

