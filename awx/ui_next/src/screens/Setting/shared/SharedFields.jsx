import React, { useState } from 'react';
import { shape, string } from 'prop-types';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import {
  FileUpload,
  FormGroup as PFFormGroup,
  InputGroup,
  Switch,
  TextArea,
  TextInput,
} from '@patternfly/react-core';
import FileUploadIcon from '@patternfly/react-icons/dist/js/icons/file-upload-icon';
import styled from 'styled-components';
import AnsibleSelect from '../../../components/AnsibleSelect';
import CodeEditor from '../../../components/CodeEditor';
import { PasswordInput } from '../../../components/FormField';
import { FormFullWidthLayout } from '../../../components/FormLayout';
import Popover from '../../../components/Popover';
import {
  combine,
  integer,
  minMaxValue,
  required,
  url,
} from '../../../util/validators';
import RevertButton from './RevertButton';

const FormGroup = styled(PFFormGroup)`
  .pf-c-form__group-label {
    display: inline-flex;
    align-items: center;
    width: 100%;
  }
`;

const SettingGroup = ({
  children,
  defaultValue,
  fieldId,
  helperTextInvalid,
  isDisabled,
  isRequired,
  label,
  onRevertCallback,
  popoverContent,
  validated,
}) => {
  return (
    <FormGroup
      fieldId={fieldId}
      helperTextInvalid={helperTextInvalid}
      id={`${fieldId}-field`}
      isRequired={isRequired}
      label={label}
      validated={validated}
      labelIcon={
        <>
          <Popover
            content={popoverContent}
            ariaLabel={`${t`More information for`} ${label}`}
          />
          <RevertButton
            id={fieldId}
            defaultValue={defaultValue}
            isDisabled={isDisabled}
            onRevertCallback={onRevertCallback}
          />
        </>
      }
    >
      {children}
    </FormGroup>
  );
};
const BooleanField = ({ ariaLabel = '', name, config, disabled = false }) => {
  const [field, meta, helpers] = useField(name);

  return config ? (
    <SettingGroup
      defaultValue={config.default ?? false}
      fieldId={name}
      helperTextInvalid={meta.error}
      isDisabled={disabled}
      label={config.label}
      popoverContent={config.help_text}
    >
      <Switch
        id={name}
        ouiaId={name}
        isChecked={field.value}
        isDisabled={disabled}
        label={t`On`}
        labelOff={t`Off`}
        onChange={checked => helpers.setValue(checked)}
        aria-label={ariaLabel || config.label}
      />
    </SettingGroup>
  ) : null;
};
BooleanField.propTypes = {
  name: string.isRequired,
  config: shape({}).isRequired,
};

const ChoiceField = ({ name, config, isRequired = false }) => {
  const validate = isRequired ? required(null) : null;
  const [field, meta] = useField({ name, validate });
  const isValid = !meta.error || !meta.touched;

  return config ? (
    <SettingGroup
      defaultValue={config.default ?? ''}
      fieldId={name}
      helperTextInvalid={meta.error}
      isRequired={isRequired}
      label={config.label}
      popoverContent={config.help_text}
      validated={isValid ? 'default' : 'error'}
    >
      <AnsibleSelect
        id={name}
        {...field}
        data={[
          ...config.choices.map(([value, label], index) => ({
            label,
            value: value ?? '',
            key: value ?? index,
          })),
        ]}
      />
    </SettingGroup>
  ) : null;
};
ChoiceField.propTypes = {
  name: string.isRequired,
  config: shape({}).isRequired,
};

const EncryptedField = ({ name, config, isRequired = false }) => {
  const validate = isRequired ? required(null) : null;
  const [, meta] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);

  return config ? (
    <SettingGroup
      defaultValue={config.default ?? ''}
      fieldId={name}
      helperTextInvalid={meta.error}
      isRequired={isRequired}
      label={config.label}
      popoverContent={config.help_text}
      validated={isValid ? 'default' : 'error'}
    >
      <InputGroup>
        <PasswordInput
          id={name}
          name={name}
          label={config.label}
          validate={validate}
          isRequired={isRequired}
        />
      </InputGroup>
    </SettingGroup>
  ) : null;
};
EncryptedField.propTypes = {
  name: string.isRequired,
  config: shape({}).isRequired,
};

const InputField = ({ name, config, type = 'text', isRequired = false }) => {
  const min_value = config?.min_value ?? Number.MIN_SAFE_INTEGER;
  const max_value = config?.max_value ?? Number.MAX_SAFE_INTEGER;
  const validators = [
    ...(isRequired ? [required(null)] : []),
    ...(type === 'url' ? [url()] : []),
    ...(type === 'number'
      ? [integer(), minMaxValue(min_value, max_value)]
      : []),
  ];
  const [field, meta] = useField({ name, validate: combine(validators) });
  const isValid = !(meta.touched && meta.error);

  return config ? (
    <SettingGroup
      defaultValue={config.default ?? ''}
      fieldId={name}
      helperTextInvalid={meta.error}
      isRequired={isRequired}
      label={config.label}
      popoverContent={config.help_text}
      validated={isValid ? 'default' : 'error'}
    >
      <TextInput
        id={name}
        isRequired={isRequired}
        placeholder={config.placeholder}
        validated={isValid ? 'default' : 'error'}
        value={field.value}
        onBlur={field.onBlur}
        onChange={(value, event) => {
          field.onChange(event);
        }}
      />
    </SettingGroup>
  ) : null;
};
InputField.propTypes = {
  name: string.isRequired,
  config: shape({}).isRequired,
};

const TextAreaField = ({ name, config, isRequired = false }) => {
  const validate = isRequired ? required(null) : null;
  const [field, meta] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);

  return config ? (
    <SettingGroup
      defaultValue={config.default || ''}
      fieldId={name}
      helperTextInvalid={meta.error}
      isRequired={isRequired}
      label={config.label}
      popoverContent={config.help_text}
      validated={isValid ? 'default' : 'error'}
    >
      <TextArea
        id={name}
        isRequired={isRequired}
        placeholder={config.placeholder}
        validated={isValid ? 'default' : 'error'}
        value={field.value}
        onBlur={field.onBlur}
        onChange={(value, event) => {
          field.onChange(event);
        }}
        resizeOrientation="vertical"
      />
    </SettingGroup>
  ) : null;
};
TextAreaField.propTypes = {
  name: string.isRequired,
  config: shape({}).isRequired,
};

const ObjectField = ({ name, config, isRequired = false }) => {
  const validate = isRequired ? required(null) : null;
  const [field, meta, helpers] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);

  const emptyDefault = config?.type === 'list' ? '[]' : '{}';
  const defaultRevertValue = config?.default
    ? JSON.stringify(config.default, null, 2)
    : emptyDefault;

  return config ? (
    <FormFullWidthLayout>
      <SettingGroup
        defaultValue={defaultRevertValue}
        fieldId={name}
        helperTextInvalid={meta.error}
        isRequired={isRequired}
        label={config.label}
        popoverContent={config.help_text}
        validated={isValid ? 'default' : 'error'}
      >
        <CodeEditor
          {...field}
          rows="auto"
          id={name}
          mode="javascript"
          onChange={value => {
            helpers.setValue(value);
          }}
          placeholder={JSON.stringify(config?.placeholder, null, 2)}
        />
      </SettingGroup>
    </FormFullWidthLayout>
  ) : null;
};
ObjectField.propTypes = {
  name: string.isRequired,
  config: shape({}).isRequired,
};

const FileUploadIconWrapper = styled.div`
  margin: var(--pf-global--spacer--md);
`;
const FileUploadField = ({
  name,
  config,
  type = 'text',
  isRequired = false,
}) => {
  const validate = isRequired ? required(null) : null;
  const [filename, setFilename] = useState('');
  const [fileIsUploading, setFileIsUploading] = useState(false);
  const [field, meta, helpers] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);

  return config ? (
    <FormFullWidthLayout>
      <SettingGroup
        defaultValue={config.default ?? ''}
        fieldId={name}
        helperTextInvalid={meta.error}
        isRequired={isRequired}
        label={config.label}
        popoverContent={config.help_text}
        validated={isValid ? 'default' : 'error'}
        onRevertCallback={() => setFilename('')}
      >
        <FileUpload
          {...field}
          id={name}
          type={type}
          filename={filename}
          onChange={(value, title) => {
            helpers.setValue(value);
            setFilename(title);
          }}
          onReadStarted={() => setFileIsUploading(true)}
          onReadFinished={() => setFileIsUploading(false)}
          isLoading={fileIsUploading}
          allowEditingUploadedText
          validated={isValid ? 'default' : 'error'}
          hideDefaultPreview={type === 'dataURL'}
        >
          {type === 'dataURL' && (
            <FileUploadIconWrapper>
              {field.value ? (
                <img
                  src={field.value}
                  alt={filename}
                  height="200px"
                  width="200px"
                />
              ) : (
                <FileUploadIcon size="lg" />
              )}
            </FileUploadIconWrapper>
          )}
        </FileUpload>
      </SettingGroup>
    </FormFullWidthLayout>
  ) : null;
};
FileUploadField.propTypes = {
  name: string.isRequired,
  config: shape({}).isRequired,
};

export {
  BooleanField,
  ChoiceField,
  EncryptedField,
  FileUploadField,
  InputField,
  ObjectField,
  TextAreaField,
};
