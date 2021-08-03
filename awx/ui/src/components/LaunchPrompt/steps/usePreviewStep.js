import React from 'react';
import { t } from '@lingui/macro';
import PreviewStep from './PreviewStep';
import StepName from './StepName';

const STEP_ID = 'preview';

export default function usePreviewStep(
  launchConfig,

  resource,
  surveyConfig,
  hasErrors,
  showStep,
  nextButtonText
) {
  return {
    step: showStep
      ? {
          id: STEP_ID,
          name: (
            <StepName hasErrors={false} id="preview-step">
              {t`Preview`}
            </StepName>
          ),
          component: (
            <PreviewStep
              launchConfig={launchConfig}
              resource={resource}
              surveyConfig={surveyConfig}
              formErrors={hasErrors}
            />
          ),
          enableNext: !hasErrors,
          nextButtonText: nextButtonText || t`Launch`,
        }
      : null,
    initialValues: {},
    isReady: true,
    error: null,
    setTouched: () => {},
    validate: () => {},
  };
}
