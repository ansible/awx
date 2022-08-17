import React from 'react';
import { t } from '@lingui/macro';
import ExecutionEnvironmentStep from './ExecutionEnvironmentStep';
import StepName from './StepName';

const STEP_ID = 'executionEnvironment';

export default function useExecutionEnvironmentStep(launchConfig, resource) {
  return {
    step: getStep(launchConfig, resource),
    initialValues: getInitialValues(launchConfig, resource),
    isReady: true,
    contentError: null,
    hasError: false,
    setTouched: (setFieldTouched) => {
      setFieldTouched('execution_environment', true, false);
    },
    validate: () => {},
  };
}
function getStep(launchConfig) {
  if (!launchConfig.ask_execution_environment_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    name: (
      <StepName id="execution-environment-step">
        {t`Execution Environment`}
      </StepName>
    ),
    component: <ExecutionEnvironmentStep />,
    enableNext: true,
  };
}

function getInitialValues(launchConfig, resource) {
  if (!launchConfig.ask_execution_environment_on_launch) {
    return {};
  }

  return {
    execution_environment:
      resource?.summary_fields?.execution_environment || null,
  };
}
