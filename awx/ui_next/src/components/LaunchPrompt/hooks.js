import { useState } from 'react';
import useInventoryStep from './steps/useInventoryStep';
import useCredentialsStep from './steps/useCredentialsStep';
import useOtherPromptsStep from './steps/useOtherPromptsStep';
import useSurveyStep from './steps/useSurveyStep';
import usePreviewStep from './steps/usePreviewStep';

export function useSteps(config, resource, i18n) {
  const [formErrors, setFormErrors] = useState({});
  const inventory = useInventoryStep(config, resource, i18n);
  const credentials = useCredentialsStep(config, resource, i18n);
  const otherPrompts = useOtherPromptsStep(config, resource, i18n);
  const survey = useSurveyStep(config, resource, i18n);
  const preview = usePreviewStep(
    config,
    resource,
    survey.survey,
    formErrors,
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

  const validate = values => {
    const errors = {
      ...inventory.validate(values),
      ...credentials.validate(values),
      ...otherPrompts.validate(values),
      ...survey.validate(values),
    };
    setFormErrors(errors);
    if (Object.keys(errors).length) {
      return errors;
    }
    return false;
  };

  return { steps, initialValues, isReady, validate, formErrors, contentError };
}

export function usePromptErrors(config) {
  const [promptErrors, setPromptErrors] = useState({});
  const updatePromptErrors = () => {};
  return [promptErrors, updatePromptErrors];
}

// TODO this interrelates with usePromptErrors
// merge? or pass result from one into the other?
export function useVisitedSteps(config) {
  return [[], () => {}];
}
