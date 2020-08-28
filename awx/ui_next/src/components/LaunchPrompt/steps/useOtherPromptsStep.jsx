import React from 'react';
import { t } from '@lingui/macro';
import OtherPromptsStep from './OtherPromptsStep';

const STEP_ID = 'other';

export default function useOtherPrompt(
  config,
  visitedSteps,
  i18n,
  loadedResource,
  currentResource
) {
  return {
    step: getStep(config, i18n),
    initialValues: getInitialValues(config, loadedResource, currentResource),
    isReady: true,
    contentError: null,
    formError: null,
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

function getStep(config, i18n) {
  if (!shouldShowPrompt(config)) {
    return null;
  }
  return {
    id: STEP_ID,
    key: 5,
    name: i18n._(t`Other Prompts`),
    component: <OtherPromptsStep config={config} i18n={i18n} />,
    enableNext: true,
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

function getInitialValues(config, loadedResource, currentResource) {
  if (!config) {
    return {};
  }

  const initialValues = {};
  if (config.ask_job_type_on_launch) {
    initialValues.job_type =
      currentResource?.job_type || loadedResource?.job_type || '';
  }
  if (config.ask_limit_on_launch) {
    initialValues.limit = currentResource?.limit || loadedResource?.limit || '';
  }
  if (config.ask_verbosity_on_launch) {
    initialValues.verbosity =
      currentResource?.verbosity || loadedResource?.verbosity || 0;
  }
  if (config.ask_tags_on_launch) {
    initialValues.job_tags =
      currentResource?.job_tags || loadedResource?.job_tags || '';
  }
  if (config.ask_skip_tags_on_launch) {
    initialValues.skip_tags =
      currentResource?.skip_tags || loadedResource?.skip_tags || '';
  }
  if (config.ask_variables_on_launch) {
    initialValues.extra_vars =
      currentResource?.extra_vars || loadedResource.extra_vars || '---';
  }
  if (config.ask_scm_branch_on_launch) {
    initialValues.scm_branch =
      currentResource?.scm_branch || loadedResource?.scm_branch || '';
  }
  if (config.ask_diff_mode_on_launch) {
    initialValues.diff_mode =
      currentResource?.diff_mode || loadedResource?.diff_mode || false;
  }
  return initialValues;
}
