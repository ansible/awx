import React from 'react';
import { useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import PreviewStep from './PreviewStep';

const STEP_ID = 'preview';

export default function usePreviewStep(
  config,
  resource,
  survey,
  hasErrors,
  i18n
) {
  const { values: formikValues, errors } = useFormikContext();

  const formErrorsContent = [];
  if (config.ask_inventory_on_launch && !formikValues.inventory) {
    formErrorsContent.push({
      inventory: true,
    });
  }
  const hasSurveyError = Object.keys(errors).find(e => e.includes('survey'));
  if (
    config.survey_enabled &&
    (config.variables_needed_to_start ||
      config.variables_needed_to_start.length === 0) &&
    hasSurveyError
  ) {
    formErrorsContent.push({
      survey: true,
    });
  }

  return {
    step: {
      id: STEP_ID,
      name: i18n._(t`Preview`),
      component: (
        <PreviewStep
          config={config}
          resource={resource}
          survey={survey}
          formErrors={hasErrors}
        />
      ),
      enableNext: !hasErrors,
      nextButtonText: i18n._(t`Launch`),
    },
    initialValues: {},
    isReady: true,
    error: null,
    setTouched: () => {},
  };
}
