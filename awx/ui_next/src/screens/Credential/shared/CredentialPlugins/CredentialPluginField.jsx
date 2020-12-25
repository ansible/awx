import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import {
  Button,
  ButtonVariant,
  FormGroup,
  InputGroup,
  Tooltip,
} from '@patternfly/react-core';
import { KeyIcon } from '@patternfly/react-icons';
import FieldWithPrompt from '../../../../components/FieldWithPrompt';
import Popover from '../../../../components/Popover';
import { CredentialPluginPrompt } from './CredentialPluginPrompt';
import CredentialPluginSelected from './CredentialPluginSelected';

function CredentialPluginInput(props) {
  const {
    children,
    i18n,
    isDisabled,
    isRequired,
    isValid,
    fieldOptions,
  } = props;

  const [showPluginWizard, setShowPluginWizard] = useState(false);
  const [inputField, , helpers] = useField(`inputs.${fieldOptions.id}`);
  const [passwordPromptField] = useField(`passwordPrompts.${fieldOptions.id}`);

  return (
    <>
      {inputField?.value?.credential ? (
        <CredentialPluginSelected
          credential={inputField?.value?.credential}
          onClearPlugin={() => helpers.setValue('')}
          onEditPlugin={() => setShowPluginWizard(true)}
        />
      ) : (
        <InputGroup>
          {React.cloneElement(children, {
            ...inputField,
            isRequired,
            validated: isValid ? 'default' : 'error',
            isDisabled: !!passwordPromptField.value,
            onChange: (_, event) => {
              inputField.onChange(event);
            },
          })}
          <Tooltip
            content={i18n._(
              t`Populate field from an external secret management system`
            )}
          >
            <Button
              id={`credential-${fieldOptions.id}-external-button`}
              variant={ButtonVariant.control}
              aria-label={i18n._(
                t`Populate field from an external secret management system`
              )}
              onClick={() => setShowPluginWizard(true)}
              isDisabled={isDisabled || !!passwordPromptField.value}
            >
              <KeyIcon />
            </Button>
          </Tooltip>
        </InputGroup>
      )}
      {showPluginWizard && (
        <CredentialPluginPrompt
          initialValues={
            typeof inputField.value === 'object' ? inputField.value : {}
          }
          onClose={() => setShowPluginWizard(false)}
          onSubmit={val => {
            val.touched = true;
            helpers.setValue(val);
            setShowPluginWizard(false);
          }}
        />
      )}
    </>
  );
}

function CredentialPluginField(props) {
  const { fieldOptions, isRequired, isValid } = props;

  const [, meta, helpers] = useField(`inputs.${fieldOptions.id}`);
  const [passwordPromptField] = useField(`passwordPrompts.${fieldOptions.id}`);

  useEffect(() => {
    if (passwordPromptField.value) {
      helpers.setValue('');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [passwordPromptField.value]);

  return (
    <>
      {fieldOptions.ask_at_runtime ? (
        <FieldWithPrompt
          fieldId={`credential-${fieldOptions.id}`}
          helperTextInvalid={meta.error}
          isRequired={isRequired}
          label={fieldOptions.label}
          promptId={`credential-prompt-${fieldOptions.id}`}
          promptName={`passwordPrompts.${fieldOptions.id}`}
          tooltip={fieldOptions.help_text}
        >
          <CredentialPluginInput {...props} />
          {meta.error && meta.touched && (
            <div
              className="pf-c-form__helper-text pf-m-error"
              id={`${fieldOptions.id}-helper`}
              aria-live="polite"
            >
              {meta.error}
            </div>
          )}
        </FieldWithPrompt>
      ) : (
        <FormGroup
          fieldId={`credential-${fieldOptions.id}`}
          helperTextInvalid={meta.error}
          isRequired={isRequired}
          validated={isValid ? 'default' : 'error'}
          label={fieldOptions.label}
          labelIcon={
            fieldOptions.help_text && (
              <Popover content={fieldOptions.help_text} />
            )
          }
        >
          <CredentialPluginInput {...props} />
        </FormGroup>
      )}
    </>
  );
}

CredentialPluginField.propTypes = {
  fieldOptions: PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
  }).isRequired,
  isDisabled: PropTypes.bool,
  isRequired: PropTypes.bool,
};

CredentialPluginField.defaultProps = {
  isDisabled: false,
  isRequired: false,
};

export default withI18n()(CredentialPluginField);
