import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import DaysToKeepStep from './DaysToKeepStep';
import StepName from '../../../../../components/LaunchPrompt/steps/StepName';

const STEP_ID = 'daysToKeep';

export default function useDaysToKeepStep() {
  const [, nodeResourceMeta] = useField('nodeResource');
  const [, daysToKeepMeta] = useField('daysToKeep');

  return {
    step: getStep(nodeResourceMeta, daysToKeepMeta),
    initialValues: { daysToKeep: 30 },
    isReady: true,
    contentError: null,
    hasError: !!daysToKeepMeta.error,
    setTouched: (setFieldTouched) => {
      setFieldTouched('daysToKeep', true, false);
    },
    validate: () => {},
  };
}
function getStep(nodeResourceMeta, daysToKeepMeta) {
  if (
    ['cleanup_activitystream', 'cleanup_jobs'].includes(
      nodeResourceMeta?.value?.job_type
    )
  ) {
    return {
      id: STEP_ID,
      name: (
        <StepName hasErrors={!!daysToKeepMeta.error} id="days-to-keep-step">
          {t`Days to keep`}
        </StepName>
      ),
      component: <DaysToKeepStep />,
      enableNext: !daysToKeepMeta.error,
    };
  }
  return null;
}
