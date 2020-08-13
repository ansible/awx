import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withFormik, useFormikContext } from 'formik';
import PropTypes from 'prop-types';

import Wizard from '../Wizard';
import AdHocCredentialStep from './AdHocCredentialStep';
import AdHocDetailsStep from './AdHocDetailsStep';

function AdHocCommandsWizard({
  onLaunch,
  i18n,
  moduleOptions,
  verbosityOptions,
  onCloseWizard,
  credentialTypeId,
}) {
  const [currentStepId, setCurrentStepId] = useState(1);
  const [enableLaunch, setEnableLaunch] = useState(false);

  const { values } = useFormikContext();

  const enabledNextOnDetailsStep = () => {
    if (!values.module_args) {
      return false;
    }

    if (values.module_args === 'shell' || values.module_args === 'command') {
      if (values.arguments) {
        return true;
        // eslint-disable-next-line no-else-return
      } else {
        return false;
      }
    }
    return undefined; // makes the linter happy;
  };
  const steps = [
    {
      id: 1,
      key: 1,
      name: i18n._(t`Details`),
      component: (
        <AdHocDetailsStep
          moduleOptions={moduleOptions}
          verbosityOptions={verbosityOptions}
        />
      ),
      enableNext: enabledNextOnDetailsStep(),
      nextButtonText: i18n._(t`Next`),
    },
    {
      id: 2,
      key: 2,
      name: i18n._(t`Machine credential`),
      component: (
        <AdHocCredentialStep
          credentialTypeId={credentialTypeId}
          onEnableLaunch={() => setEnableLaunch(true)}
        />
      ),
      enableNext: enableLaunch,
      nextButtonText: i18n._(t`Launch`),
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
      title={i18n._(t`Run command`)}
      nextButtonText={currentStep.nextButtonText || undefined}
      backButtonText={i18n._(t`Back`)}
      cancelButtonText={i18n._(t`Cancel`)}
    />
  );
}

const FormikApp = withFormik({
  mapPropsToValues({ adHocItems, verbosityOptions }) {
    const adHocItemStrings = adHocItems.map(item => item.name).join(', ');
    return {
      limit: adHocItemStrings || [],
      credential: [],
      module_args: '',
      arguments: '',
      verbosity: verbosityOptions[0].value,
      forks: 0,
      changes: false,
      escalation: false,
      extra_vars: '---',
    };
  },
})(AdHocCommandsWizard);

FormikApp.propTypes = {
  onLaunch: PropTypes.func.isRequired,
  moduleOptions: PropTypes.arrayOf(PropTypes.object).isRequired,
  verbosityOptions: PropTypes.arrayOf(PropTypes.object).isRequired,
  onCloseWizard: PropTypes.func.isRequired,
  credentialTypeId: PropTypes.number.isRequired,
};
export default withI18n()(FormikApp);
