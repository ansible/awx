import { useState } from 'react';
import useInventoryStep from './steps/useInventoryStep';
import useCredentialsStep from './steps/useCredentialsStep';
import useOtherPromptsStep from './steps/useOtherPromptsStep';
import useSurveyStep from './steps/useSurveyStep';
import usePreviewStep from './steps/usePreviewStep';

export default function useSteps(config, resource, i18n) {
  const [visited, setVisited] = useState({});
  const inventory = useInventoryStep(config, resource, visited, i18n);
  const credentials = useCredentialsStep(config, resource, visited, i18n);
  const otherPrompts = useOtherPromptsStep(config, resource, visited, i18n);
  const survey = useSurveyStep(config, resource, visited, i18n);
  const preview = usePreviewStep(
    config,
    resource,
    survey.survey,
    {}, // TODO: formErrors ?
    i18n
  );

  // TODO useState for steps to track dynamic steps (credentialPasswords)?
  const steps = [
    inventory.step,
    credentials.step,
    otherPrompts.step,
    survey.step,
    preview.step,
  ].filter(step => step !== null);
  const initialValues = {
    ...inventory.initialValues,
    ...credentials.initialValues,
    ...otherPrompts.initialValues,
    ...survey.initialValues,
  };
  const isReady =
    inventory.isReady &&
    credentials.isReady &&
    otherPrompts.isReady &&
    survey.isReady &&
    preview.isReady;
  const contentError =
    inventory.error ||
    credentials.error ||
    otherPrompts.error ||
    survey.error ||
    preview.error;

  // TODO: store error state in each step's hook.
  // but continue to return values here (async?) so form errors can be returned
  // out and set into Formik
  const validate = values => {
    const errors = {
      ...inventory.validate(values),
      ...credentials.validate(values),
      ...otherPrompts.validate(values),
      ...survey.validate(values),
    };
    // setFormErrors(errors);
    if (Object.keys(errors).length) {
      return errors;
    }
    return false;
  };

  // TODO move visited flags into each step hook
  return {
    steps,
    initialValues,
    isReady,
    validate,
    visitStep: stepId => setVisited({ ...visited, [stepId]: true }),
    visitAllSteps: () => {
      setVisited({
        inventory: true,
        credentials: true,
        other: true,
        survey: true,
        preview: true,
      });
    },
    contentError,
  };
}
