import React from 'react';
import { t } from '@lingui/macro';
import PreviewStep from './PreviewStep';

const STEP_ID = 'preview';

export default function usePreviewStep(
  config,
  i18n,
  resource,
  survey,
  hasErrors,
  needsPreviewStep
) {
  const showStep =
    needsPreviewStep && resource && Object.keys(config).length > 0;
  return {
    step: showStep
      ? {
          id: STEP_ID,
          key: 7,
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
        }
      : null,
    initialValues: {},
    validate: () => ({}),
    isReady: true,
    error: null,
    setTouched: () => {},
  };
}
