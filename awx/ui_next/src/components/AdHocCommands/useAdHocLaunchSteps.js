import { useState } from 'react';
import useAdHocDetailsStep from './useAdHocDetailsStep';
import useAdHocExecutionEnvironmentStep from './useAdHocExecutionEnvironmentStep';
import useAdHocCredentialStep from './useAdHocCredentialStep';
import useAdHocPreviewStep from './useAdHocPreviewStep';

export default function useAdHocLaunchSteps(
  moduleOptions,
  verbosityOptions,
  organizationId,
  credentialTypeId
) {
  const [visited, setVisited] = useState({});
  const steps = [
    useAdHocDetailsStep(visited, moduleOptions, verbosityOptions),
    useAdHocExecutionEnvironmentStep(organizationId),
    useAdHocCredentialStep(visited, credentialTypeId),
  ];

  const hasErrors = steps.some((step) => step.hasError);

  steps.push(useAdHocPreviewStep(hasErrors));
  return {
    steps: steps.map((s) => s.step).filter((s) => s != null),
    validateStep: (stepId) =>
      steps.find((s) => s?.step.id === stepId).validate(),
    visitStep: (prevStepId, setFieldTouched) => {
      setVisited({
        ...visited,
        [prevStepId]: true,
      });
      steps.find((s) => s?.step?.id === prevStepId).setTouched(setFieldTouched);
    },
    visitAllSteps: (setFieldTouched) => {
      setVisited({
        details: true,
        executionEnvironment: true,
        credential: true,
        preview: true,
      });
      steps.forEach((s) => s.setTouched(setFieldTouched));
    },
  };
}
