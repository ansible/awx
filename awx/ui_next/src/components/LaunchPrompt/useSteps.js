import { useState } from 'react';
import useInventoryStep from './steps/useInventoryStep';
import useCredentialsStep from './steps/useCredentialsStep';
import useOtherPromptsStep from './steps/useOtherPromptsStep';
import useSurveyStep from './steps/useSurveyStep';
import usePreviewStep from './steps/usePreviewStep';

export default function useSteps(config, resource, i18n) {
  const [visited, setVisited] = useState({});
  const steps = [
    useInventoryStep(config, resource, visited, i18n),
    useCredentialsStep(config, resource, visited, i18n),
    useOtherPromptsStep(config, resource, visited, i18n),
    useSurveyStep(config, resource, visited, i18n),
  ];

  const formErrorsContent = steps
    .filter(s => s?.formError && Object.keys(s.formError).length > 0)
    .map(({ formError }) => formError);

  steps.push(
    usePreviewStep(config, resource, steps[3].survey, formErrorsContent, i18n)
  );

  const pfSteps = steps.map(s => s.step).filter(s => s != null);
  const initialValues = steps.reduce((acc, cur) => {
    return {
      ...acc,
      ...cur.initialValues,
    };
  }, {});
  const isReady = !steps.some(s => !s.isReady);

  const stepWithError = steps.find(s => s.contentError);
  const contentError = stepWithError ? stepWithError.contentError : null;

  const validate = values => {
    const errors = steps.reduce((acc, cur) => {
      return {
        ...acc,
        ...cur.validate(values),
      };
    }, {});
    if (Object.keys(errors).length) {
      return errors;
    }
    return false;
  };

  return {
    steps: pfSteps,
    initialValues,
    isReady,
    validate,
    visitStep: stepId => setVisited({ ...visited, [stepId]: true }),
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
