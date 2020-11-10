import React, { useState } from 'react';
import { useField, useFormikContext } from 'formik';
import { shape, string } from 'prop-types';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  FileUpload as PFFileUpload,
  FormGroup,
  InputGroup,
  TextInput,
} from '@patternfly/react-core';
import { PasswordInput } from '../../../../components/FormField';
import AnsibleSelect from '../../../../components/AnsibleSelect';
import Popover from '../../../../components/Popover';
import { CredentialType } from '../../../../types';
import { required } from '../../../../util/validators';
import { CredentialPluginField } from '../CredentialPlugins';
import BecomeMethodField from './BecomeMethodField';

const FileUpload = styled(PFFileUpload)`
  flex-grow: 1;
`;

function CredentialInput({ fieldOptions, credentialKind, ...rest }) {
  const [fileName, setFileName] = useState('');
  const [fileIsUploading, setFileIsUploading] = useState(false);
  const [subFormField, meta, helpers] = useField(`inputs.${fieldOptions.id}`);
  const isValid = !(meta.touched && meta.error);
  if (fieldOptions.multiline) {
    const handleFileChange = (value, filename) => {
      helpers.setValue(value);
      setFileName(filename);
    };

    return (
      <FileUpload
        {...subFormField}
        id={`credential-${fieldOptions.id}`}
        type="text"
        filename={fileName}
        onChange={handleFileChange}
        onReadStarted={() => setFileIsUploading(true)}
        onReadFinished={() => setFileIsUploading(false)}
        isLoading={fileIsUploading}
        allowEditingUploadedText
        validated={isValid ? 'default' : 'error'}
      />
    );
  }
  if (fieldOptions.secret) {
    const passwordInput = () => (
      <PasswordInput
        {...subFormField}
        id={`credential-${fieldOptions.id}`}
        {...rest}
      />
    );
    return credentialKind === 'external' ? (
      <InputGroup>{passwordInput()}</InputGroup>
    ) : (
      passwordInput()
    );
  }
  return (
    <TextInput
      {...subFormField}
      id={`credential-${fieldOptions.id}`}
      onChange={(value, event) => {
        subFormField.onChange(event);
      }}
      validated={isValid ? 'default' : 'error'}
    />
  );
}

CredentialInput.propTypes = {
  fieldOptions: shape({
    id: string.isRequired,
    label: string.isRequired,
  }).isRequired,
  credentialKind: string,
};

CredentialInput.defaultProps = {
  credentialKind: '',
};

function CredentialField({ credentialType, fieldOptions, i18n }) {
  const { values: formikValues } = useFormikContext();
  const requiredFields = credentialType?.inputs?.required || [];
  const isRequired = requiredFields.includes(fieldOptions.id);
  const validateField = () => {
    if (isRequired && !formikValues?.passwordPrompts[fieldOptions.id]) {
      const validationMsg = fieldOptions.ask_at_runtime
        ? i18n._(
            t`Provide a value for this field or select the Prompt on launch option.`
          )
        : null;
      return required(validationMsg, i18n);
    }
    return null;
  };
  const [subFormField, meta, helpers] = useField({
    name: `inputs.${fieldOptions.id}`,
    validate: validateField(),
  });
  const isValid = !(meta.touched && meta.error);

  if (fieldOptions.choices) {
    const selectOptions = fieldOptions.choices.map(choice => {
      return {
        value: choice,
        key: choice,
        label: choice,
      };
    });
    return (
      <FormGroup
        fieldId={`credential-${fieldOptions.id}`}
        helperTextInvalid={meta.error}
        label={fieldOptions.label}
        isRequired={isRequired}
        validated={isValid ? 'default' : 'error'}
      >
        <AnsibleSelect
          {...subFormField}
          id={`credential-${fieldOptions.id}`}
          data={selectOptions}
          onChange={(event, value) => {
            helpers.setValue(value);
          }}
        />
      </FormGroup>
    );
  }
  if (credentialType.kind === 'external') {
    return (
      <FormGroup
        fieldId={`credential-${fieldOptions.id}`}
        helperTextInvalid={meta.error}
        label={fieldOptions.label}
        labelIcon={
          fieldOptions.help_text && <Popover content={fieldOptions.help_text} />
        }
        isRequired={isRequired}
        validated={isValid ? 'default' : 'error'}
      >
        <CredentialInput
          credentialKind={credentialType.kind}
          fieldOptions={fieldOptions}
        />
      </FormGroup>
    );
  }
  if (credentialType.kind === 'ssh' && fieldOptions.id === 'become_method') {
    return (
      <BecomeMethodField fieldOptions={fieldOptions} isRequired={isRequired} />
    );
  }
  return (
    <CredentialPluginField
      fieldOptions={fieldOptions}
      isRequired={isRequired}
      validated={isValid ? 'default' : 'error'}
    >
      <CredentialInput fieldOptions={fieldOptions} />
    </CredentialPluginField>
  );
}

CredentialField.propTypes = {
  credentialType: CredentialType.isRequired,
  fieldOptions: shape({
    id: string.isRequired,
    label: string.isRequired,
  }).isRequired,
};

CredentialField.defaultProps = {};

export default withI18n()(CredentialField);
