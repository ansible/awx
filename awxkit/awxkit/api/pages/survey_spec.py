from . import base
from . import page

from awxkit.api.resources import resources


class SurveySpec(base.Base):

    def get_variable_default(self, var):
        for item in self.spec:
            if item.get('variable') == var:
                return item.get('default')

    def get_default_vars(self):
        default_vars = dict()
        for item in self.spec:
            if item.get("default", None):
                default_vars[item.variable] = item.default
        return default_vars

    def get_required_vars(self):
        required_vars = []
        for item in self.spec:
            if item.get("required", None):
                required_vars.append(item.variable)
        return required_vars


page.register_page([resources.job_template_survey_spec,
                    resources.workflow_job_template_survey_spec], SurveySpec)
