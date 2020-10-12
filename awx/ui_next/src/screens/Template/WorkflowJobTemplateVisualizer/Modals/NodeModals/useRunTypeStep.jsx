import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';

import RunStep from './RunStep';

const STEP_ID = 'runType';

export default function useRunTypeStep(i18n, askLinkType) {
  const [, meta] = useField('linkType');

  return {
    step: getStep(askLinkType, meta, i18n),
    initialValues: askLinkType ? { linkType: 'success' } : {},
    isReady: true,
    contentError: null,
    formError: meta.error,
    setTouched: setFieldsTouched => {
      setFieldsTouched({
        inventory: true,
      });
    },
  };
}
function getStep(askLinkType, meta, i18n) {
  if (!askLinkType) {
    return null;
  }
  return {
    id: STEP_ID,
    key: 1,
    name: i18n._(t`Run Type`),
    component: <RunStep />,
    enableNext: meta.value !== '',
  };
}
