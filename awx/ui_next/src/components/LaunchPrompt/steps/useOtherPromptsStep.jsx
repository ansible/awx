import React from 'react';
import { t } from '@lingui/macro';
import OtherPromptsStep from './OtherPromptsStep';

const STEP_ID = 'other';

export default function useOtherPrompt(config, resource, i18n) {
  return {
    step: getStep(config, i18n),
    initialValues: getInitialValues(config, resource),
    isReady: true,
    error: null,
  };
}

function getStep(config, i18n) {
  if (!shouldShowPrompt(config)) {
    return null;
  }
  return {
    id: STEP_ID,
    name: i18n._(t`Other Prompts`),
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
