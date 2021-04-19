import React, { useState } from 'react';
import { t } from '@lingui/macro';
import { ExclamationCircleIcon as PFExclamationCircleIcon } from '@patternfly/react-icons';
import { Tooltip } from '@patternfly/react-core';
import { withFormik, useFormikContext } from 'formik';
import PropTypes from 'prop-types';

import styled from 'styled-components';
import Wizard from '../Wizard';
import AdHocCredentialStep from './AdHocCredentialStep';
import AdHocDetailsStep from './AdHocDetailsStep';

const AlertText = styled.div`
  color: var(--pf-global--danger-color--200);
  font-weight: var(--pf-global--FontWeight--bold);
`;

const ExclamationCircleIcon = styled(PFExclamationCircleIcon)`
  margin-left: 10px;
  color: var(--pf-global--danger-color--100);
`;

function AdHocCommandsWizard({
  onLaunch,
  moduleOptions,
  verbosityOptions,
  onCloseWizard,
  credentialTypeId,
}) {
  const [currentStepId, setCurrentStepId] = useState(1);
  const [enableLaunch, setEnableLaunch] = useState(false);

  const { values, errors, touched } = useFormikContext();

  const enabledNextOnDetailsStep = () => {
    if (!values.module_name) {
      return false;
    }

    if (values.module_name === 'shell' || values.module_name === 'command') {
      if (values.module_args) {
        return true;
        // eslint-disable-next-line no-else-return
      } else {
        return false;
      }
    }
    return undefined; // makes the linter happy;
  };
  const hasDetailsStepError = errors.module_args && touched.module_args;

  const steps = [
    {
      id: 1,
      key: 1,
      name: hasDetailsStepError ? (
        <AlertText>
          {t`Details`}
          <Tooltip
            position="right"
            content={t`This step contains errors`}
            trigger="click mouseenter focus"
          >
            <ExclamationCircleIcon />
          </Tooltip>
        </AlertText>
      ) : (
        t`Details`
      ),
      component: (
        <AdHocDetailsStep
          moduleOptions={moduleOptions}
          verbosityOptions={verbosityOptions}
        />
      ),
      enableNext: enabledNextOnDetailsStep(),
      nextButtonText: t`Next`,
    },
    {
      id: 2,
      key: 2,
      name: t`Machine credential`,
      component: (
        <AdHocCredentialStep
          credentialTypeId={credentialTypeId}
          onEnableLaunch={() => setEnableLaunch(true)}
        />
      ),
      enableNext: enableLaunch && Object.values(errors).length === 0,
      nextButtonText: t`Launch`,
      canJumpTo: currentStepId >= 2,
    },
  ];

  const currentStep = steps.find(step => step.id === currentStepId);

  return (
    <Wizard
      style={{ overflow: 'scroll' }}
      isOpen
      onNext={step => setCurrentStepId(step.id)}
      onClose={() => onCloseWizard()}
      onSave={() => {
        onLaunch(values);
      }}
      steps={steps}
      title={t`Run command`}
      nextButtonText={currentStep.nextButtonText || undefined}
      backButtonText={t`Back`}
      cancelButtonText={t`Cancel`}
    />
  );
}

const FormikApp = withFormik({
  mapPropsToValues({ adHocItems, verbosityOptions }) {
    const adHocItemStrings = adHocItems.map(item => item.name).join(', ');
    return {
      limit: adHocItemStrings || 'all',
      credential: [],
      module_args: '',
      verbosity: verbosityOptions[0].value,
      forks: 0,
      diff_mode: false,
      become_enabled: '',
      module_name: '',
      extra_vars: '---',
      job_type: 'run',
    };
  },
})(AdHocCommandsWizard);

FormikApp.propTypes = {
  onLaunch: PropTypes.func.isRequired,
  moduleOptions: PropTypes.arrayOf(PropTypes.array).isRequired,
  verbosityOptions: PropTypes.arrayOf(PropTypes.object).isRequired,
  onCloseWizard: PropTypes.func.isRequired,
  credentialTypeId: PropTypes.number.isRequired,
};
export default FormikApp;
