import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withFormik, useFormikContext } from 'formik';

import Wizard from '../Wizard';
import AdHocCredentialStep from './AdHocCredentialStep';
import DetailsStep from './DetailsStep';

function AdHocCommandsWizard({
  onLaunch,
  i18n,
  moduleOptions,
  verbosityOptions,
  onCloseWizard,
  credentialTypeId,
}) {
  const [currentStepId, setCurrentStepId] = useState(1);
  const [limitTypedValue, setLimitTypedValue] = useState('');
  const [enableLaunch, setEnableLaunch] = useState(false);

  const { values } = useFormikContext();

  const steps = [
    {
      id: 1,
      key: 1,
      name: i18n._(t`Details`),
      component: (
        <DetailsStep
          moduleOptions={moduleOptions}
          verbosityOptions={verbosityOptions}
          onLimitChange={value => setLimitTypedValue(value)}
          limitValue={limitTypedValue}
        />
      ),
      enableNext: values.module_args && values.arguments && values.verbosity,
      nextButtonText: i18n._(t`Next`),
    },
    {
      id: 2,
      key: 2,
      name: i18n._(t`Machine Credential`),
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

  const submit = () => {
    onLaunch(values, limitTypedValue);
  };

  return (
    <Wizard
      style={{ overflow: 'scroll' }}
      isOpen
      onNext={step => setCurrentStepId(step.id)}
      onClose={() => onCloseWizard()}
      onSave={submit}
      steps={steps}
      title={i18n._(t`Ad Hoc Commands`)}
      nextButtonText={currentStep.nextButtonText || undefined}
      backButtonText={i18n._(t`Back`)}
      cancelButtonText={i18n._(t`Cancel`)}
    />
  );
}

const FormikApp = withFormik({
  mapPropsToValues({ adHocItems }) {
    const adHocItemStrings = adHocItems.map(item => item.name);
    return {
      limit: adHocItemStrings || [],
      credential: [],
      module_args: '',
      arguments: '',
      verbosity: '',
      forks: 0,
      changes: false,
      escalation: false,
      extra_vars: '---',
    };
  },
})(AdHocCommandsWizard);

export default withI18n()(FormikApp);
