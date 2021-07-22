import React from 'react';
import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import StepName from '../LaunchPrompt/steps/StepName';
import AdHocPreviewStep from './AdHocPreviewStep';

const STEP_ID = 'preview';
export default function useAdHocPreviewStep(hasErrors) {
  const { values } = useFormikContext();

  return {
    step: {
      id: STEP_ID,
      key: 4,
      name: (
        <StepName hasErrors={false} id="preview-step">
          {t`Preview`}
        </StepName>
      ),
      component: <AdHocPreviewStep hasErrors={hasErrors} values={values} />,
      enableNext: !hasErrors,
      nextButtonText: t`Launch`,
    },
    hasErrors: false,
    validate: () => {},
    setTouched: () => {},
  };
}
