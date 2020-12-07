import React from 'react';
import { t } from '@lingui/macro';
import PreviewStep from './PreviewStep';

const STEP_ID = 'preview';

export default function usePreviewStep(
  launchConfig,
  i18n,
  resource,
  surveyConfig,
  hasErrors,
  showStep
) {
  return {
    step: showStep
      ? {
          id: STEP_ID,
          name: i18n._(t`Preview`),
          component: (
            <PreviewStep
              launchConfig={launchConfig}
              resource={resource}
              surveyConfig={surveyConfig}
              formErrors={hasErrors}
            />
          ),
          enableNext: !hasErrors,
          nextButtonText: i18n._(t`Launch`),
        }
      : null,
    initialValues: {},
    validate: () => ({}),
    isReady: true,
    error: null,
    setTouched: () => {},
  };
}
