/* eslint-disable react/jsx-no-useless-fragment */
import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useField, useFormikContext } from 'formik';
import { shape, string } from 'prop-types';
import styled from 'styled-components';

import { t } from '@lingui/macro';
import {
  Button,
  ButtonVariant,
  FileUpload as PFFileUpload,
  FormGroup,
  InputGroup,
  TextInput,
  Tooltip,
} from '@patternfly/react-core';
import { PficonHistoryIcon } from '@patternfly/react-icons';
import { PasswordInput } from 'components/FormField';
import AnsibleSelect from 'components/AnsibleSelect';
import Popover from 'components/Popover';
import { CredentialType } from 'types';
import { required } from 'util/validators';
import { CredentialPluginField } from '../CredentialPlugins';
import BecomeMethodField from './BecomeMethodField';

const FileUpload = styled(PFFileUpload)`
  flex-grow: 1;
`;

function CredentialInput({
  fieldOptions,
  isFieldGroupValid,
  credentialKind,
  isVaultIdDisabled,
  ...rest
}) {
  const [fileName, setFileName] = useState('');
  const [fileIsUploading, setFileIsUploading] = useState(false);
  const [subFormField, meta, helpers] = useField(`inputs.${fieldOptions.id}`);
  const [passwordPromptsField] = useField(`passwordPrompts.${fieldOptions.id}`);
  const isValid = !(meta.touched && meta.error);

  const RevertReplaceButton = (
    <>
      {meta.initialValue &&
        meta.initialValue !== '' &&
        !meta.initialValue.credential &&
        !passwordPromptsField.value && (
          <Tooltip
            id={`credential-${fieldOptions.id}-replace-tooltip`}
            content={meta.value !== meta.initialValue ? t`Revert` : t`Replace`}
          >
            <Button
              id={`credential-${fieldOptions.id}-replace-button`}
              variant={ButtonVariant.control}
              aria-label={
                meta.touched
                  ? t`Revert field to previously saved value`
                  : t`Replace field with new value`
              }
              onClick={() => {
                if (meta.value !== meta.initialValue) {
                  helpers.setValue(meta.initialValue);
                } else {
                  helpers.setValue('', false);
                }
              }}
            >
              <PficonHistoryIcon />
            </Button>
          </Tooltip>
        )}
    </>
  );

  if (fieldOptions.multiline) {
    const handleFileChange = (value, filename) => {
      helpers.setValue(value);
      setFileName(filename);
    };

    if (fieldOptions.secret) {
      return (
        <InputGroup>
          {RevertReplaceButton}
          <FileUpload
            {...subFormField}
            {...rest}
            id={`credential-${fieldOptions.id}`}
            type="text"
            filename={fileName}
            filenamePlaceholder={t`Drag a file here or browse to upload`}
            browseButtonText={t`Browse…`}
            clearButtonText={t`Clear`}
            onChange={handleFileChange}
            onReadStarted={() => setFileIsUploading(true)}
            onReadFinished={() => setFileIsUploading(false)}
            isLoading={fileIsUploading}
            allowEditingUploadedText
            validated={isValid ? 'default' : 'error'}
          />
        </InputGroup>
      );
    }

    return (
      <FileUpload
        {...subFormField}
        {...rest}
        id={`credential-${fieldOptions.id}`}
        type="text"
        filename={fileName}
        filenamePlaceholder={t`Drag a file here or browse to upload`}
        browseButtonText={t`Browse…`}
        clearButtonText={t`Clear`}
        onChange={handleFileChange}
        onReadStarted={() => setFileIsUploading(true)}
        onReadFinished={() => setFileIsUploading(false)}
        isLoading={fileIsUploading}
        allowEditingUploadedText
        validated={isValid ? 'default' : 'error'}
        isDisabled={false}
      />
    );
  }

  if (fieldOptions.secret) {
    const passwordInput = () => (
      <>
        {RevertReplaceButton}
        <PasswordInput
          isFieldGroupValid={isFieldGroupValid}
          {...subFormField}
          id={`credential-${fieldOptions.id}`}
          {...rest}
        />
      </>
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
      isDisabled={isVaultIdDisabled}
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

function CredentialField({ credentialType, fieldOptions }) {
  const { values: formikValues } = useFormikContext();
  const location = useLocation();
  const requiredFields = credentialType?.inputs?.required || [];
  const isRequired = requiredFields.includes(fieldOptions.id);
  const validateField = () => {
    if (isRequired && !formikValues?.passwordPrompts[fieldOptions.id]) {
      const validationMsg = fieldOptions.ask_at_runtime
        ? t`Provide a value for this field or select the Prompt on launch option.`
        : null;
      return required(validationMsg);
    }
    return null;
  };
  const [subFormField, meta, helpers] = useField({
    name: `inputs.${fieldOptions.id}`,
    validate: validateField(),
  });
  const isValid =
    !(meta.touched && meta.error) ||
    formikValues.passwordPrompts[fieldOptions.id];

  if (fieldOptions.choices) {
    const selectOptions = fieldOptions.choices.map((choice) => ({
      value: choice,
      key: choice,
      label: choice,
    }));
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
          isDisabled={
            !!(
              meta.initialValue &&
              meta.initialValue !== '' &&
              meta.value === meta.initialValue
            )
          }
        />
      </FormGroup>
    );
  }
  if (credentialType.kind === 'ssh' && fieldOptions.id === 'become_method') {
    return (
      <BecomeMethodField fieldOptions={fieldOptions} isRequired={isRequired} />
    );
  }

  let disabled = false;
  if (
    credentialType.kind === 'vault' &&
    location.pathname.endsWith('edit') &&
    fieldOptions.id === 'vault_id'
  ) {
    disabled = true;
  }
  return (
    <CredentialPluginField
      fieldOptions={fieldOptions}
      isRequired={isRequired}
      validated={isValid ? 'default' : 'error'}
    >
      <CredentialInput
        isFieldGroupValid={isValid}
        fieldOptions={fieldOptions}
        isVaultIdDisabled={disabled}
      />
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

export default CredentialField;
