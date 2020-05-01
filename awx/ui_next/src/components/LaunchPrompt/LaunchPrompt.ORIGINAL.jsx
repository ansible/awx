import React, { useState, useCallback, useEffect } from 'react';
import { Wizard } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik } from 'formik';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '@api';
import useRequest from '@util/useRequest';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { required } from '@util/validators';
import InventoryStep from './InventoryStep';
import CredentialsStep from './CredentialsStep';
import OtherPromptsStep from './OtherPromptsStep';
import SurveyStep from './SurveyStep';
import PreviewStep from './PreviewStep';
import PromptFooter from './PromptFooter';
import mergeExtraVars from './mergeExtraVars';

const STEPS = {
  INVENTORY: 'inventory',
  CREDENTIALS: 'credentials',
  PASSWORDS: 'passwords',
  OTHER_PROMPTS: 'other',
  SURVEY: 'survey',
  PREVIEW: 'preview',
};

function showOtherPrompts(config) {
  return (
    config.ask_job_type_on_launch ||
    config.ask_limit_on_launch ||
    config.ask_verbosity_on_launch ||
    config.ask_tags_on_launch ||
    config.ask_skip_tags_on_launch ||
    config.ask_variables_on_launch ||
    config.ask_scm_branch_on_launch ||
    config.ask_diff_mode_on_launch
  );
}

function getInitialVisitedSteps(config) {
  const visited = {};
  if (config.ask_inventory_on_launch) {
    visited[STEPS.INVENTORY] = false;
  }
  if (config.ask_credential_on_launch) {
    visited[STEPS.CREDENTIALS] = false;
  }
  if (showOtherPrompts(config)) {
    visited[STEPS.OTHER_PROMPTS] = false;
  }
  if (config.survey_enabled) {
    visited[STEPS.SURVEY] = false;
  }
  return visited;
}

function LaunchPrompt({ config, resource, onLaunch, onCancel, i18n }) {
  const [formErrors, setFormErrors] = useState({});
  const [visitedSteps, setVisitedSteps] = useState(
    getInitialVisitedSteps(config)
  );

  const {
    result: survey,
    request: fetchSurvey,
    error: surveyError,
  } = useRequest(
    useCallback(async () => {
      if (!config.survey_enabled) {
        return {};
      }
      const { data } =
        resource.type === 'workflow_job_template'
          ? await WorkflowJobTemplatesAPI.readSurvey(resource.id)
          : await JobTemplatesAPI.readSurvey(resource.id);
      return data;
    }, [config.survey_enabled, resource])
  );
  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey]);

  if (surveyError) {
    return <ContentError error={surveyError} />;
  }
  if (config.survey_enabled && !survey) {
    return <ContentLoading />;
  }

  const steps = [];
  const initialValues = {};
  if (config.ask_inventory_on_launch) {
    initialValues.inventory = resource?.summary_fields?.inventory || null;
    steps.push({
      id: STEPS.INVENTORY,
      name: i18n._(t`Inventory`),
      component: <InventoryStep />,
    });
  }
  if (config.ask_credential_on_launch) {
    initialValues.credentials = resource?.summary_fields?.credentials || [];
    steps.push({
      id: STEPS.CREDENTIALS,
      name: i18n._(t`Credentials`),
      component: <CredentialsStep />,
    });
  }

  // TODO: Add Credential Passwords step

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
  if (showOtherPrompts(config)) {
    steps.push({
      id: STEPS.OTHER_PROMPTS,
      name: i18n._(t`Other Prompts`),
      component: <OtherPromptsStep config={config} />,
    });
  }
  if (config.survey_enabled) {
    initialValues.survey = {};
    // survey.spec.forEach(question => {
    //   initialValues[`survey_${question.variable}`] = question.default;
    // })
    steps.push({
      id: STEPS.SURVEY,
      name: i18n._(t`Survey`),
      component: <SurveyStep survey={survey} />,
    });
  }
  steps.push({
    id: STEPS.PREVIEW,
    name: i18n._(t`Preview`),
    component: (
      <PreviewStep
        resource={resource}
        config={config}
        survey={survey}
        formErrors={formErrors}
      />
    ),
    enableNext: Object.keys(formErrors).length === 0,
    nextButtonText: i18n._(t`Launch`),
  });

  const validate = values => {
    // return {};
    return { limit: ['required field'] };
  };

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
    setValue('extra_vars', mergeExtraVars(values.extra_vars, values.survey));
    onLaunch(postValues);
  };
  console.log('formErrors:', formErrors);

  return (
    <Formik initialValues={initialValues} onSubmit={submit} validate={validate}>
      {({ errors, values, touched, validateForm, handleSubmit }) => (
        <Wizard
          isOpen
          onClose={onCancel}
          onSave={handleSubmit}
          onNext={async (nextStep, prevStep) => {
            // console.log(`${prevStep.prevName} -> ${nextStep.name}`);
            // console.log('errors', errors);
            // console.log('values', values);
            const newErrors = await validateForm();
            setFormErrors(newErrors);
            // console.log('new errors:', newErrors);
          }}
          onGoToStep={async (newStep, prevStep) => {
            // console.log('errors', errors);
            // console.log('values', values);
            const newErrors = await validateForm();
            setFormErrors(newErrors);
          }}
          title={i18n._(t`Prompts`)}
          steps={steps}
          // footer={<PromptFooter firstStep={steps[0].id} />}
        />
      )}
    </Formik>
  );
}

export { LaunchPrompt as _LaunchPrompt };
export default withI18n()(LaunchPrompt);
