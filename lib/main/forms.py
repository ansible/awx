import json
from django import forms
from django.utils.translation import ugettext_lazy as _
from jsonfield.fields import JSONFormField
from lib.main.models import *


EMPTY_CHOICE = ('', '---------')

class PlaybookOption(object):

    def __init__(self, project, playbook):
        self.project, self.playbook = project, playbook

    def __unicode__(self):
        return self.playbook

class PlaybookSelect(forms.Select):
    '''Custom select widget for playbooks related to a project.'''

    def render_option(self, selected_choices, option_value, obj):
        opt = super(PlaybookSelect, self).render_option(selected_choices,
                                                        option_value,
                                                        unicode(obj))
        # Add a class with the project ID so JS can filter the options.
        if hasattr(obj, 'project'):
            opt = opt.replace('">', '" class="project-%s">' % obj.project.pk)
        return opt

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

class JobTemplateAdminForm(forms.ModelForm):
    '''Custom admin form for creating/editing JobTemplates.'''

    playbook = forms.ChoiceField(choices=[EMPTY_CHOICE], widget=PlaybookSelect)
    
    class Meta:
        model = JobTemplate

    def __init__(self, *args, **kwargs):
        super(JobTemplateAdminForm, self).__init__(*args, **kwargs)
        playbook_choices = []
        for project in Project.objects.all():
            for playbook in project.available_playbooks:
                playbook_choices.append((playbook,
                                         PlaybookOption(project, playbook)))
        self.fields['playbook'].choices = [EMPTY_CHOICE] + playbook_choices

class JobAdminForm(JobTemplateAdminForm):
    '''Custom admin form for creating Jobs.'''

    start_job = forms.BooleanField(initial=False, required=False)
    ssh_password = forms.CharField(label=_('SSH password'), required=False)
    sudo_password = forms.CharField(required=False)
    ssh_key_unlock = forms.CharField(label=_('SSH key passphrase'),
                                     required=False)
    cancel_job = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = Job

    def __init__(self, *args, **kwargs):
        super(JobAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk and self.instance.status != 'new':
            self.fields.pop('playbook', None)
        if (not self.data or self.data.get('start_job', '')) and \
                self.instance.credential and self.instance.status == 'new':
            for field in self.instance.get_passwords_needed_to_start():
                if field not in self.fields:
                    continue
                self.fields[field].required = True

    def clean_start_job(self):
        return self.cleaned_data.get('start_job', False)

    def clean_cancel_job(self):
        return self.cleaned_data.get('cancel_job', False)

    def clean(self):
        if self.instance.credential and self.instance.status == 'new':
            for field in self.instance.get_passwords_needed_to_start():
                if field in self.fields:
                    self.fields[field].required = True
        return super(JobAdminForm, self).clean()

    def save(self, commit=True):
        instance = super(JobAdminForm, self).save(commit)
        save_m2m = getattr(self, 'save_m2m', lambda: None)
        should_start = bool(self.cleaned_data.get('start_job', '') and
                            instance.status == 'new')
        start_opts = {}
        for field in ('ssh_password', 'sudo_password', 'ssh_key_unlock'):
            value = self.cleaned_data.get(field, '')
            if value:
                start_opts[field] = value
        #print 'should_start', should_start
        should_cancel = bool(self.cleaned_data.get('cancel_job', '') and
                             instance.status in ('new', 'pending'))
        def new_save_m2m():
            save_m2m()
            if should_start:
                instance.start(**start_opts)
            if should_cancel:
                instance.cancel()
        if commit:
            new_save_m2m()
        else:
            self.save_m2m = new_save_m2m
        return instance
