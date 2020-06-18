import React from 'react';
import { func, shape } from 'prop-types';
import { Formik, useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Wizard } from '@patternfly/react-core';
import CredentialsStep from './CredentialsStep';
import MetadataStep from './MetadataStep';

function CredentialPluginWizard({ i18n, handleSubmit, onClose }) {
  const [selectedCredential] = useField('credential');
  const steps = [
    {
      id: 1,
      name: i18n._(t`Credential`),
      component: <CredentialsStep />,
      enableNext: !!selectedCredential.value,
    },
    {
      id: 2,
      name: i18n._(t`Metadata`),
      component: <MetadataStep />,
      canJumpTo: !!selectedCredential.value,
      nextButtonText: i18n._(t`OK`),
    },
  ];

  return (
    <Wizard
      isOpen
      onClose={onClose}
      title={i18n._(t`External Secret Management System`)}
      steps={steps}
      onSave={handleSubmit}
    />
  );
}

function CredentialPluginPrompt({ i18n, onClose, onSubmit, initialValues }) {
  return (
    <Formik
      initialValues={{
        credential: initialValues?.credential || null,
        inputs: initialValues?.inputs || {},
      }}
      onSubmit={onSubmit}
    >
      {({ handleSubmit }) => (
        <CredentialPluginWizard
          handleSubmit={handleSubmit}
          i18n={i18n}
          onClose={onClose}
        />
      )}
    </Formik>
  );
}

CredentialPluginPrompt.propTypes = {
  onClose: func.isRequired,
  onSubmit: func.isRequired,
  initialValues: shape({}),
};

CredentialPluginPrompt.defaultProps = {
  initialValues: {},
};

export default withI18n()(CredentialPluginPrompt);
