import { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import useInventoryStep from './steps/useInventoryStep';
import useCredentialsStep from './steps/useCredentialsStep';
import useOtherPromptsStep from './steps/useOtherPromptsStep';
import useSurveyStep from './steps/useSurveyStep';
import usePreviewStep from './steps/usePreviewStep';

export default function useLaunchSteps(
  launchConfig,
  surveyConfig,
  resource,
  i18n
) {
  const [visited, setVisited] = useState({});
  const [isReady, setIsReady] = useState(false);
  const steps = [
    useInventoryStep(launchConfig, resource, i18n, visited),
    useCredentialsStep(launchConfig, resource, i18n),
    useOtherPromptsStep(launchConfig, resource, i18n),
    useSurveyStep(launchConfig, surveyConfig, resource, i18n, visited),
  ];
  const { resetForm } = useFormikContext();
  const hasErrors = steps.some(step => step.formError);

  steps.push(
    usePreviewStep(launchConfig, i18n, resource, surveyConfig, hasErrors, true)
  );

  const pfSteps = steps.map(s => s.step).filter(s => s != null);
  const stepsAreReady = !steps.some(s => !s.isReady);

  useEffect(() => {
    if (stepsAreReady) {
      const initialValues = steps.reduce((acc, cur) => {
        return {
          ...acc,
          ...cur.initialValues,
        };
      }, {});
      resetForm({
        values: {
          ...initialValues,
        },
      });

      setIsReady(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stepsAreReady]);

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
