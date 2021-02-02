import { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import useInventoryStep from '../../LaunchPrompt/steps/useInventoryStep';
import useCredentialsStep from '../../LaunchPrompt/steps/useCredentialsStep';
import useOtherPromptsStep from '../../LaunchPrompt/steps/useOtherPromptsStep';
import useSurveyStep from '../../LaunchPrompt/steps/useSurveyStep';
import usePreviewStep from '../../LaunchPrompt/steps/usePreviewStep';

export default function useSchedulePromptSteps(
  surveyConfig,
  launchConfig,
  schedule,
  resource,
  i18n,
  scheduleCredentials
) {
  const {
    summary_fields: { credentials: resourceCredentials },
  } = resource;
  const sourceOfValues =
    (Object.keys(schedule).length > 0 && schedule) || resource;

  sourceOfValues.summary_fields = {
    credentials: [...resourceCredentials, ...scheduleCredentials],
    ...sourceOfValues.summary_fields,
  };
  const { resetForm, values } = useFormikContext();
  const [visited, setVisited] = useState({});

  const steps = [
    useInventoryStep(launchConfig, sourceOfValues, i18n, visited),
    useCredentialsStep(launchConfig, sourceOfValues, i18n),
    useOtherPromptsStep(launchConfig, sourceOfValues, i18n),
    useSurveyStep(launchConfig, surveyConfig, sourceOfValues, i18n, visited),
  ];

  const hasErrors = steps.some(step => step.hasError);
  steps.push(
    usePreviewStep(
      launchConfig,
      i18n,
      resource,
      surveyConfig,
      hasErrors,
      true,
      i18n._(t`Save`)
    )
  );

  const pfSteps = steps.map(s => s.step).filter(s => s != null);
  const isReady = !steps.some(s => !s.isReady);

  useEffect(() => {
    let initialValues = {};
    if (launchConfig && surveyConfig && isReady) {
      initialValues = steps.reduce((acc, cur) => {
        return {
          ...acc,
          ...cur.initialValues,
        };
      }, {});
    }
    resetForm({
      values: {
        ...initialValues,
        ...values,
      },
    });

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [launchConfig, surveyConfig, isReady]);

  const stepWithError = steps.find(s => s.contentError);
  const contentError = stepWithError ? stepWithError.contentError : null;

  return {
    isReady,
    validateStep: stepId => {
      steps.find(s => s?.step?.id === stepId).validate();
    },
    steps: pfSteps,
    visitStep: (prevStepId, setFieldTouched) => {
      setVisited({
        ...visited,
        [prevStepId]: true,
      });
      steps.find(s => s?.step?.id === prevStepId).setTouched(setFieldTouched);
    },
    visitAllSteps: setFieldTouched => {
      setVisited({
        inventory: true,
        credentials: true,
        other: true,
        survey: true,
        preview: true,
      });
      steps.forEach(s => s.setTouched(setFieldTouched));
    },
    contentError,
  };
}
