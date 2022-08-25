import { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import useInventoryStep from '../../LaunchPrompt/steps/useInventoryStep';
import useCredentialsStep from '../../LaunchPrompt/steps/useCredentialsStep';
import useExecutionEnvironmentStep from '../../LaunchPrompt/steps/useExecutionEnvironmentStep';
import useInstanceGroupsStep from '../../LaunchPrompt/steps/useInstanceGroupsStep';
import useOtherPromptsStep from '../../LaunchPrompt/steps/useOtherPromptsStep';
import useSurveyStep from '../../LaunchPrompt/steps/useSurveyStep';
import usePreviewStep from '../../LaunchPrompt/steps/usePreviewStep';

export default function useSchedulePromptSteps(
  surveyConfig,
  launchConfig,
  schedule,
  resource,
  scheduleCredentials,
  resourceDefaultCredentials,
  labels
) {
  const sourceOfValues =
    (Object.keys(schedule).length > 0 && schedule) || resource;
  const { resetForm, values } = useFormikContext();
  const [visited, setVisited] = useState({});

  const steps = [
    useInventoryStep(launchConfig, sourceOfValues, visited),
    useCredentialsStep(
      launchConfig,
      sourceOfValues,
      resourceDefaultCredentials
    ),
    useExecutionEnvironmentStep(launchConfig, resource),
    useInstanceGroupsStep(launchConfig, resource),
    useOtherPromptsStep(launchConfig, sourceOfValues, labels),
    useSurveyStep(launchConfig, surveyConfig, sourceOfValues, visited),
  ];

  const hasErrors = steps.some((step) => step.hasError);

  steps.push(
    usePreviewStep(
      launchConfig,
      resource,
      surveyConfig,
      hasErrors,
      true,
      t`Save`
    )
  );

  const pfSteps = steps.map((s) => s.step).filter((s) => s != null);
  const isReady = !steps.some((s) => !s.isReady);

  useEffect(() => {
    if (launchConfig && surveyConfig && isReady) {
      let initialValues = {};
      initialValues = steps.reduce(
        (acc, cur) => ({
          ...acc,
          ...cur.initialValues,
        }),
        {}
      );

      if (launchConfig.ask_credential_on_launch) {
        const defaultCredsWithoutOverrides = [];

        const credentialHasOverride = (templateDefaultCred) => {
          let hasOverride = false;
          scheduleCredentials.forEach((scheduleCredential) => {
            if (
              templateDefaultCred.credential_type ===
              scheduleCredential.credential_type
            ) {
              if (
                (!templateDefaultCred.inputs.vault_id &&
                  !scheduleCredential.inputs.vault_id) ||
                (templateDefaultCred.inputs.vault_id &&
                  scheduleCredential.inputs.vault_id &&
                  templateDefaultCred.inputs.vault_id ===
                    scheduleCredential.inputs.vault_id)
              ) {
                hasOverride = true;
              }
            }
          });

          return hasOverride;
        };

        if (resourceDefaultCredentials) {
          resourceDefaultCredentials.forEach((defaultCred) => {
            if (!credentialHasOverride(defaultCred)) {
              defaultCredsWithoutOverrides.push(defaultCred);
            }
          });
        }

        initialValues.credentials = scheduleCredentials.concat(
          defaultCredsWithoutOverrides
        );
      }

      resetForm({
        values: {
          ...initialValues,
          ...values,
        },
      });
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [launchConfig, surveyConfig, isReady]);

  const stepWithError = steps.find((s) => s.contentError);
  const contentError = stepWithError ? stepWithError.contentError : null;

  return {
    isReady,
    validateStep: (stepId) => {
      steps.find((s) => s?.step?.id === stepId).validate();
    },
    steps: pfSteps,
    visitStep: (prevStepId, setFieldTouched) => {
      setVisited({
        ...visited,
        [prevStepId]: true,
      });
      steps.find((s) => s?.step?.id === prevStepId).setTouched(setFieldTouched);
    },
    visitAllSteps: (setFieldTouched) => {
      setVisited({
        inventory: true,
        credentials: true,
        executionEnvironment: true,
        instanceGroups: true,
        other: true,
        survey: true,
        preview: true,
      });
      steps.forEach((s) => s.setTouched(setFieldTouched));
    },
    contentError,
  };
}
