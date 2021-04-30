import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import RunStep from './RunStep';
import StepName from '../../../../../components/LaunchPrompt/steps/StepName';

const STEP_ID = 'runType';

export default function useRunTypeStep(askLinkType) {
  const [, meta] = useField('linkType');

  return {
    step: getStep(askLinkType, meta),
    initialValues: askLinkType ? { linkType: 'success' } : {},
    isReady: true,
    contentError: null,
    hasError: !!meta.error,
    setTouched: setFieldTouched => {
      setFieldTouched('linkType', true, false);
    },
    validate: () => {},
  };
}
function getStep(askLinkType, meta) {
  if (!askLinkType) {
    return null;
  }
  return {
    id: STEP_ID,
    name: (
      <StepName hasErrors={false} id="run-type-step">
        {t`Run type`}
      </StepName>
    ),
    component: <RunStep />,
    enableNext: meta.value !== '',
  };
}
