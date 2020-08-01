import React, { useState } from 'react';
import { t } from '@lingui/macro';
import OtherPromptsStep from './OtherPromptsStep';
import StepName from './StepName';

const STEP_ID = 'other';

export default function useOtherPrompt(config, resource, visitedSteps, i18n) {
  const [stepErrors, setStepErrors] = useState({});

  const validate = values => {
    const errors = {};
    if (config.ask_job_type_on_launch && !values.job_type) {
      errors.job_type = i18n._(t`This field must not be blank`);
    }
    setStepErrors(errors);
    return errors;
  };

  const hasErrors = visitedSteps[STEP_ID] && Object.keys(stepErrors).length > 0;

  return {
    step: getStep(config, hasErrors, i18n),
    initialValues: getInitialValues(config, resource),
    validate,
    isReady: true,
    contentError: null,
    formError: stepErrors,
    setTouched: setFieldsTouched => {
      setFieldsTouched({
        job_type: true,
        limit: true,
        verbosity: true,
        diff_mode: true,
        job_tags: true,
        skip_tags: true,
        extra_vars: true,
      });
    },
  };
}

function getStep(config, hasErrors, i18n) {
  if (!shouldShowPrompt(config)) {
    return null;
  }
  return {
    id: STEP_ID,
    name: <StepName hasErrors={hasErrors}>{i18n._(t`Other Prompts`)}</StepName>,
    component: <OtherPromptsStep config={config} i18n={i18n} />,
  };
}

function shouldShowPrompt(config) {
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

function getInitialValues(config, resource) {
  const initialValues = {};
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
  return initialValues;
}
