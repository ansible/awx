import { useState } from 'react';
import useInventoryStep from './steps/useInventoryStep';
import useCredentialsStep from './steps/useCredentialsStep';
import useOtherPromptsStep from './steps/useOtherPromptsStep';
import useSurveyStep from './steps/useSurveyStep';
import usePreviewStep from './steps/usePreviewStep';

// const INVENTORY = 'inventory';
// const CREDENTIALS = 'credentials';
// const PASSWORDS = 'passwords';
// const OTHER_PROMPTS = 'other';
// const SURVEY = 'survey';
// const PREVIEW = 'preview';

export function useSteps(config, resource, i18n) {
  // TODO pass in form errors?
  const formErrors = {};
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

  return { steps, initialValues, isReady, contentError };
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
