import { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import useInventoryStep from '../../../../../components/LaunchPrompt/steps/useInventoryStep';
import useCredentialsStep from '../../../../../components/LaunchPrompt/steps/useCredentialsStep';
import useOtherPromptsStep from '../../../../../components/LaunchPrompt/steps/useOtherPromptsStep';
import useSurveyStep from '../../../../../components/LaunchPrompt/steps/useSurveyStep';
import usePreviewStep from '../../../../../components/LaunchPrompt/steps/usePreviewStep';
import useNodeTypeStep from './NodeTypeStep/useNodeTypeStep';
import useRunTypeStep from './useRunTypeStep';

export default function useWorkflowNodeSteps(
  config,
  i18n,
  resource,
  askLinkType,
  needsPreviewStep,
  nodeToEdit
) {
  const [visited, setVisited] = useState({});
  const steps = [
    useRunTypeStep(i18n, askLinkType),
    useNodeTypeStep(i18n, nodeToEdit),
    useInventoryStep(
      config,
      i18n,
      visited,
      resource,
      nodeToEdit?.originalNodeObject
    ),
    useCredentialsStep(config, i18n, resource, nodeToEdit?.originalNodeObject),
    useOtherPromptsStep(config, i18n, resource, nodeToEdit?.originalNodeObject),
    useSurveyStep(
      config,
      i18n,
      visited,
      resource,
      nodeToEdit?.originalNodeObject
    ),
  ];

  const { resetForm, values: formikValues } = useFormikContext();
  const hasErrors = steps.some(step => step.formError);
  const surveyStepIndex = steps.findIndex(step => step.survey);
  steps.push(
    usePreviewStep(
      config,
      i18n,
      resource,
      steps[surveyStepIndex]?.survey,
      hasErrors,
      needsPreviewStep
    )
  );

  const pfSteps = steps.map(s => s.step).filter(s => s != null);
  const isReady = !steps.some(s => !s.isReady);
  const initialValues = steps.reduce((acc, cur) => {
    return {
      ...acc,
      ...cur.initialValues,
    };
  }, {});
  useEffect(() => {
    if (isReady) {
      resetForm({
        values: {
          ...initialValues,
          nodeResource: formikValues.nodeResource,
          nodeType: formikValues.nodeType || initialValues.nodeType,
          linkType: formikValues.linkType || 'success',
          verbosity: initialValues?.verbosity?.toString(),
        },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config, isReady]);

  const stepWithError = steps.find(s => s.contentError);
  const contentError = stepWithError ? stepWithError.contentError : null;

  return {
    steps: pfSteps,
    initialValues,
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
