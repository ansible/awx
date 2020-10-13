import { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import useInventoryStep from './steps/useInventoryStep';
import useCredentialsStep from './steps/useCredentialsStep';
import useOtherPromptsStep from './steps/useOtherPromptsStep';
import useSurveyStep from './steps/useSurveyStep';
import usePreviewStep from './steps/usePreviewStep';

export default function useLaunchSteps(config, resource, i18n) {
  const [visited, setVisited] = useState({});
  const steps = [
    useInventoryStep(config, visited, i18n),
    useCredentialsStep(config, i18n),
    useOtherPromptsStep(config, i18n),
    useSurveyStep(config, visited, i18n),
  ];
  const { resetForm, values: formikValues } = useFormikContext();
  const hasErrors = steps.some(step => step.formError);

  const surveyStepIndex = steps.findIndex(step => step.survey);
  steps.push(
    usePreviewStep(
      config,
      resource,
      steps[surveyStepIndex]?.survey,
      hasErrors,
      i18n
    )
  );

  const pfSteps = steps.map(s => s.step).filter(s => s != null);
  const isReady = !steps.some(s => !s.isReady);

  useEffect(() => {
    if (surveyStepIndex > -1 && isReady) {
      resetForm({
        values: {
          ...formikValues,
          ...steps[surveyStepIndex].initialValues,
        },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isReady]);

  const stepWithError = steps.find(s => s.contentError);
  const contentError = stepWithError ? stepWithError.contentError : null;

  return {
    steps: pfSteps,
    isReady,
    visitStep: stepId =>
      setVisited({
        ...visited,
        [stepId]: true,
      }),
    visitAllSteps: setFieldsTouched => {
      setVisited({
        inventory: true,
        credentials: true,
        other: true,
        survey: true,
        preview: true,
      });
      steps.forEach(s => s.setTouched(setFieldsTouched));
    },
    contentError,
  };
}
