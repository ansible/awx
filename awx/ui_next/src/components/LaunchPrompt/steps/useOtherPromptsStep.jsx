import React from 'react';
import { t } from '@lingui/macro';
import OtherPromptsStep from './OtherPromptsStep';

const STEP_ID = 'other';

export default function useOtherPrompt(config, i18n) {
  return {
    step: getStep(config, i18n),
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
