import React from 'react';
import { t } from '@lingui/macro';
import PreviewStep from './PreviewStep';

const STEP_ID = 'preview';

export default function usePreviewStep(
  config,
  loadedResource,
  survey,
  formErrors,
  i18n,
  currentResource,
  needsPreviewStep
) {
  const resource = loadedResource || currentResource;
  const showStep =
    resource && needsPreviewStep && Object.keys(config).length > 0;

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
              formErrors={formErrors}
            />
          ),
          enableNext: Object.keys(formErrors).length === 0,
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
