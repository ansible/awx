import React from 'react';
import { t } from '@lingui/macro';
import { jsonToYaml, parseVariableField } from '../../../util/yaml';
import OtherPromptsStep from './OtherPromptsStep';
import StepName from './StepName';

const STEP_ID = 'other';

const getVariablesData = resource => {
  if (resource?.extra_data) {
    return jsonToYaml(JSON.stringify(resource.extra_data));
  }
  if (resource?.extra_vars && resource?.extra_vars !== '---') {
    return jsonToYaml(JSON.stringify(parseVariableField(resource.extra_vars)));
  }
  return '---';
};

export default function useOtherPromptsStep(launchConfig, resource, i18n) {
  return {
    step: getStep(launchConfig, i18n),
    initialValues: getInitialValues(launchConfig, resource),
    isReady: true,
    contentError: null,
    hasError: false,
    setTouched: setFieldTouched => {
      [
        'job_type',
        'limit',
        'verbosity',
        'diff_mode',
        'job_tags',
        'skip_tags',
        'extra_vars',
      ].forEach(field => setFieldTouched(field, true, false));
    },
    validate: () => {},
  };
}

function getStep(launchConfig, i18n) {
  if (!shouldShowPrompt(launchConfig)) {
    return null;
  }
  return {
    id: STEP_ID,
    key: 5,
    name: (
      <StepName hasErrors={false} id="other-prompts-step">
        {i18n._(t`Other prompts`)}
      </StepName>
    ),
    component: <OtherPromptsStep launchConfig={launchConfig} i18n={i18n} />,
    enableNext: true,
  };
}

function shouldShowPrompt(launchConfig) {
  return (
    launchConfig.ask_job_type_on_launch ||
    launchConfig.ask_limit_on_launch ||
    launchConfig.ask_verbosity_on_launch ||
    launchConfig.ask_tags_on_launch ||
    launchConfig.ask_skip_tags_on_launch ||
    launchConfig.ask_variables_on_launch ||
    launchConfig.ask_scm_branch_on_launch ||
    launchConfig.ask_diff_mode_on_launch
  );
}

function getInitialValues(launchConfig, resource) {
  const initialValues = {};

  if (!launchConfig) {
    return initialValues;
  }

  if (launchConfig.ask_job_type_on_launch) {
    initialValues.job_type = resource?.job_type || '';
  }
  if (launchConfig.ask_limit_on_launch) {
    initialValues.limit = resource?.limit || '';
  }
  if (launchConfig.ask_verbosity_on_launch) {
    initialValues.verbosity = resource?.verbosity || 0;
  }
  if (launchConfig.ask_tags_on_launch) {
    initialValues.job_tags = resource?.job_tags || '';
  }
  if (launchConfig.ask_skip_tags_on_launch) {
    initialValues.skip_tags = resource?.skip_tags || '';
  }
  if (launchConfig.ask_variables_on_launch) {
    initialValues.extra_vars = getVariablesData(resource);
  }
  if (launchConfig.ask_scm_branch_on_launch) {
    initialValues.scm_branch = resource?.scm_branch || '';
  }
  if (launchConfig.ask_diff_mode_on_launch) {
    initialValues.diff_mode = resource?.diff_mode || false;
  }
  return initialValues;
}
