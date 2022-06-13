import React from 'react';
import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import StepName from '../LaunchPrompt/steps/StepName';
import AdHocDetailsStep from './AdHocDetailsStep';

const STEP_ID = 'details';
export default function useAdHocDetailsStep(
  visited,
  moduleOptions,
  verbosityOptions
) {
  const { values, touched, setFieldError } = useFormikContext();

  const hasError = () => {
    if (!Object.keys(visited).includes(STEP_ID)) {
      return false;
    }
    if (!values.module_name && touched.module_name) {
      return true;
    }

    if (values.module_name === 'shell' || values.module_name === 'command') {
      if (values.module_args) {
        return false;
        // eslint-disable-next-line no-else-return
      } else {
        return true;
      }
    }
    return false;
  };
  return {
    step: {
      id: STEP_ID,
      key: 1,
      name: (
        <StepName hasErrors={hasError()} id="details-step">
          {t`Details`}
        </StepName>
      ),
      component: (
        <AdHocDetailsStep
          moduleOptions={moduleOptions}
          verbosityOptions={verbosityOptions}
        />
      ),
      enableNext: true,
      nextButtonText: t`Next`,
    },
    hasError: hasError(),
    validate: () => {
      if (Object.keys(touched).includes('module_name' || 'module_args')) {
        if (!values.module_name) {
          setFieldError('module_name', t`This field must not be blank.`);
        }
        if (
          values.module_name === ('command' || 'shell') &&
          !values.module_args
        ) {
          setFieldError('module_args', t`This field must not be blank`);
        }
      }
    },
    setTouched: (setFieldTouched) => {
      setFieldTouched('module_name', true, false);
      setFieldTouched('module_args', true, false);
    },
  };
}
