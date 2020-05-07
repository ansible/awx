import React from 'react';
import { t } from '@lingui/macro';
import PreviewStep from './PreviewStep';

const STEP_ID = 'preview';

export default function usePreviewStep(
  config,
  resource,
  survey,
  formErrors,
  i18n
) {
  return {
    step: {
      id: STEP_ID,
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
    },
    initialValues: {},
    validate: () => ({}),
    isReady: true,
    error: null,
    setTouched: () => {},
  };
}
