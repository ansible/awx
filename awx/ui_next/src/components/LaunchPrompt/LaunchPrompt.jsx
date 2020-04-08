import React from 'react';
import { Wizard } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik } from 'formik';
import InventoryStep from './InventoryStep';
import CredentialsStep from './CredentialsStep';
import OtherPromptsStep from './OtherPromptsStep';
import SurveyStep from './SurveyStep';
import PreviewStep from './PreviewStep';

function LaunchPrompt({ config, resource, onLaunch, onCancel, i18n }) {
  const steps = [];
  const initialValues = {};
  if (config.ask_inventory_on_launch) {
    initialValues.inventory = resource?.summary_fields?.inventory || null;
    steps.push({
      name: i18n._(t`Inventory`),
      component: <InventoryStep />,
    });
  }
  if (config.ask_credential_on_launch) {
    initialValues.credentials = resource?.summary_fields?.credentials || [];
    steps.push({
      name: i18n._(t`Credentials`),
      component: <CredentialsStep />,
    });
  }

  // TODO: Add Credential Passwords step

  if (
    config.ask_job_type_on_launch ||
    config.ask_limit_on_launch ||
    config.ask_verbosity_on_launch ||
    config.ask_tags_on_launch ||
    config.ask_skip_tags_on_launch ||
    config.ask_variables_on_launch ||
    config.ask_scm_branch_on_launch ||
    config.ask_diff_mode_on_launch
  ) {
    if (config.ask_job_type_on_launch) {
      initialValues.job_type = resource.job_type || '';
    }
    if (config.ask_limit_on_launch) {
      initialValues.limit = resource.limit || '';
    }
    if (config.ask_verbosity_on_launch) {
      initialValues.verbosity = resource.verbosity || 0;
    }
    if (config.ask_tags_on_launch) {
      initialValues.job_tags = resource.job_tags || '';
    }
    if (config.ask_skip_tags_on_launch) {
      initialValues.skip_tags = resource.skip_tags || '';
    }
    if (config.ask_variables_on_launch) {
      initialValues.extra_vars = resource.extra_vars || '---';
    }
    if (config.ask_scm_branch_on_launch) {
      initialValues.scm_branch = resource.scm_branch || '';
    }
    if (config.ask_diff_mode_on_launch) {
      initialValues.diff_mode = resource.diff_mode || false;
    }
    steps.push({
      name: i18n._(t`Other Prompts`),
      component: <OtherPromptsStep config={config} />,
    });
  }
  if (config.survey_enabled) {
    steps.push({
      name: i18n._(t`Survey`),
      component: <SurveyStep />,
    });
  }
  steps.push({
    name: i18n._(t`Preview`),
    component: <PreviewStep />,
    nextButtonText: i18n._(t`Launch`),
  });

  const submit = values => {
    const postValues = {};
    const setValue = (key, value) => {
      if (typeof value !== 'undefined' && value !== null) {
        postValues[key] = value;
      }
    };
    setValue('inventory_id', values.inventory?.id);
    setValue('credentials', values.credentials?.map(c => c.id));
    setValue('job_type', values.job_type);
    setValue('limit', values.limit);
    setValue('job_tags', values.job_tags);
    setValue('skip_tags', values.skip_tags);
    setValue('extra_vars', values.extra_vars);
    onLaunch(postValues);
  };

  return (
    <Formik initialValues={initialValues} onSubmit={submit}>
      {({ handleSubmit }) => (
        <Wizard
          isOpen
          onClose={onCancel}
          onSave={handleSubmit}
          title={i18n._(t`Prompts`)}
          steps={steps}
        />
      )}
    </Formik>
  );
}

export { LaunchPrompt as _LaunchPrompt };
export default withI18n()(LaunchPrompt);
