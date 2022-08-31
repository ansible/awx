import React, { useState } from 'react';
import { shape, string } from 'prop-types';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import {
  Button,
  FileUpload,
  FormGroup as PFFormGroup,
  InputGroup,
  Switch,
  TextArea,
  TextInput,
  Tooltip,
  ButtonVariant,
} from '@patternfly/react-core';
import FileUploadIcon from '@patternfly/react-icons/dist/js/icons/file-upload-icon';
import { ExclamationCircleIcon as PFExclamationCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import AnsibleSelect from 'components/AnsibleSelect';
import { ExecutionEnvironmentLookup } from 'components/Lookup';
import CodeEditor from 'components/CodeEditor';
import { PasswordInput } from 'components/FormField';
import { FormFullWidthLayout } from 'components/FormLayout';
import Popover from 'components/Popover';
import { combine, minMaxValue, required, url, number } from 'util/validators';
import AlertModal from 'components/AlertModal';
import RevertButton from './RevertButton';

const ExclamationCircleIcon = styled(PFExclamationCircleIcon)`
  && {
    color: var(--pf-global--danger-color--100);
  }
`;

const FormGroup = styled(PFFormGroup)`
  .pf-c-form__group-label {
    display: inline-flex;
    align-items: center;
    width: 100%;
  }
`;

const Selected = styled.div`
  display: flex;
  justify-content: space-between;
  background-color: white;
  border-bottom-color: var(--pf-global--BorderColor--200);
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
}) => (
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
const BooleanField = ({
  ariaLabel = '',
  name,
  config,
  disabled = false,
  needsConfirmationModal,
  modalTitle,
}) => {
  const [field, meta, helpers] = useField(name);
  const [isModalOpen, setIsModalOpen] = useState(false);

  return config ? (
    <SettingGroup
      defaultValue={config.default ?? false}
      fieldId={name}
      helperTextInvalid={meta.error}
      isDisabled={disabled}
      label={config.label}
      popoverContent={config.help_text}
    >
      {isModalOpen && (
        <AlertModal
          isOpen
          title={modalTitle}
          variant="danger"
          aria-label={modalTitle}
          onClose={() => {
            setIsModalOpen(false);
          }}
          actions={[
            <Button
              ouiaId="confirm-misc-settings-modal"
              key="confirm"
              variant="danger"
              aria-label={t`Confirm`}
              onClick={() => {
                helpers.setValue(true);
                setIsModalOpen(false);
              }}
            >
              {t`Confirm`}
            </Button>,
            <Button
              ouiaId="cancel-misc-settings-modal"
              key="cancel"
              variant="link"
              aria-label={t`Cancel`}
              onClick={() => {
                helpers.setValue(false);
                setIsModalOpen(false);
              }}
            >
              {t`Cancel`}
            </Button>,
          ]}
        >{t`Are you sure you want to disable local authentication?  Doing so could impact users' ability to log in and the system administrator's ability to reverse this change.`}</AlertModal>
      )}
      <Switch
        id={name}
        ouiaId={name}
        isChecked={field.value}
        isDisabled={disabled}
        label={t`On`}
        labelOff={t`Off`}
        onChange={(isOn) => {
          if (needsConfirmationModal && isOn) {
            setIsModalOpen(true);
          }
          helpers.setValue(!field.value);
        }}
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

const ExecutionEnvField = ({ name, config, isRequired = false }) => {
  const [field, meta, helpers] = useField({ name });
  return config ? (
    <SettingGroup
      defaultValue={config.default ?? ''}
      fieldId={name}
      helperTextInvalid={meta.error}
      isRequired={isRequired}
      label={config.label}
      popoverContent={config.help_text}
      isDisabled={field.value === null}
      onRevertCallback={() => helpers.setValue(config.default)}
    >
      <ExecutionEnvironmentLookup
        value={field.value}
        onChange={(value) => {
          helpers.setValue(value, false);
        }}
        overrideLabel
        fieldName={name}
      />
    </SettingGroup>
  ) : null;
};
ExecutionEnvField.propTypes = {
  name: string.isRequired,
  config: shape({}).isRequired,
};

const InputAlertField = ({ name, config }) => {
  const [field, meta] = useField({ name });
  const isValid = !(meta.touched && meta.error);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDisable, setIsDisable] = useState(true);

  const handleSetIsOpen = () => {
    setIsModalOpen(true);
  };

  const handleEnableTextInput = () => {
    setIsDisable(false);
  };

  return config ? (
    <>
      <SettingGroup
        defaultValue={config.default ?? ''}
        fieldId={name}
        helperTextInvalid={meta.error}
        label={config.label}
        popoverContent={config.help_text}
        validated={isValid ? 'default' : 'error'}
        isDisabled={isDisable}
      >
        <Selected>
          {isDisable && (
            <Tooltip
              content={t`Edit Login redirect override URL`}
              position="top"
            >
              <Button
                onClick={() => {
                  handleSetIsOpen();
                }}
                ouiaId="confirm-edit-login-redirect"
                variant={ButtonVariant.control}
              >
                <ExclamationCircleIcon />
              </Button>
            </Tooltip>
          )}
          <TextInput
            id={name}
            placeholder={config.placeholder}
            validated={isValid ? 'default' : 'error'}
            value={field.value}
            onBlur={field.onBlur}
            onChange={(value, event) => {
              field.onChange(event);
            }}
            isDisabled={isDisable}
          />
        </Selected>
      </SettingGroup>
      {isModalOpen && isDisable && (
        <AlertModal
          isOpen
          title={t`Edit login redirect override URL`}
          variant="danger"
          aria-label={t`Edit login redirect override URL`}
          onClose={() => {
            setIsModalOpen(false);
          }}
          actions={[
            <Button
              key="confirm"
              variant="danger"
              aria-label={t`confirm edit login redirect`}
              onClick={() => {
                handleEnableTextInput();
                setIsModalOpen(false);
              }}
            >
              {t`Confirm`}
            </Button>,
            <Button
              key="cancel"
              variant="link"
              aria-label={t`cancel edit login redirect`}
              onClick={() => {
                setIsModalOpen(false);
              }}
            >
              {t`Cancel`}
            </Button>,
          ]}
        >
          {t`Are you sure you want to edit login redirect override URL?  Doing so could impact users' ability to log in to the system once local authentication is also disabled.`}
        </AlertModal>
      )}
    </>
  ) : null;
};

InputAlertField.propTypes = {
  name: string.isRequired,
  config: shape({}).isRequired,
};

const InputField = ({ name, config, type = 'text', isRequired = false }) => {
  const min_value = config?.min_value ?? Number.MIN_SAFE_INTEGER;
  const max_value = config?.max_value ?? Number.MAX_SAFE_INTEGER;
  const validators = [
    ...(isRequired ? [required(null)] : []),
    ...(type === 'url' ? [url()] : []),
    ...(type === 'number' ? [number(), minMaxValue(min_value, max_value)] : []),
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
        type={type}
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

const ObjectField = ({ name, config, revertValue, isRequired = false }) => {
  const validate = isRequired ? required(null) : null;
  const [field, meta, helpers] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);

  const defaultRevertValue = config?.default
    ? JSON.stringify(config.default, null, 2)
    : null;

  return config ? (
    <FormFullWidthLayout>
      <SettingGroup
        defaultValue={revertValue ?? defaultRevertValue}
        fieldId={name}
        helperTextInvalid={meta.error}
        isRequired={isRequired}
        label={config.label}
        popoverContent={config.help_text}
        validated={isValid ? 'default' : 'error'}
      >
        <CodeEditor
          {...field}
          value={
            field.value === null
              ? JSON.stringify(field.value, null, 2)
              : field.value
          }
          rows={field.value !== null ? 'auto' : 1}
          id={name}
          mode="javascript"
          onChange={(value) => {
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
  ExecutionEnvField,
  FileUploadField,
  InputField,
  ObjectField,
  TextAreaField,
  InputAlertField,
};
