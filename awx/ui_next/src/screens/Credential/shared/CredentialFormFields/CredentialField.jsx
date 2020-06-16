import React from 'react';
import { useField, useFormikContext } from 'formik';
import { shape, string } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  FormGroup,
  InputGroup,
  TextArea,
  TextInput,
} from '@patternfly/react-core';
import { FieldTooltip, PasswordInput } from '../../../../components/FormField';
import AnsibleSelect from '../../../../components/AnsibleSelect';
import { CredentialType } from '../../../../types';
import { required } from '../../../../util/validators';
import { CredentialPluginField } from './CredentialPlugins';
import BecomeMethodField from './BecomeMethodField';

function CredentialInput({ fieldOptions, credentialKind, ...rest }) {
  const [subFormField, meta] = useField(`inputs.${fieldOptions.id}`);
  const isValid = !(meta.touched && meta.error);
  if (fieldOptions.multiline) {
    return (
      <TextArea
        {...subFormField}
        id={`credential-${fieldOptions.id}`}
        rows={6}
        resizeOrientation="vertical"
        onChange={(value, event) => {
          subFormField.onChange(event);
        }}
        isValid={isValid}
      />
    );
  }
  if (fieldOptions.secret) {
    const passwordInput = () => (
      <PasswordInput
        {...subFormField}
        id={`credential-${fieldOptions.id}`}
        isValid={isValid}
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
      isValid={isValid}
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
        isValid={isValid}
      >
        <AnsibleSelect
          {...subFormField}
          id="credential_type"
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
        isRequired={isRequired}
        isValid={isValid}
      >
        {fieldOptions.help_text && (
          <FieldTooltip content={fieldOptions.help_text} />
        )}
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
      isValid={isValid}
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
