import React, { useState } from 'react';
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
import { CredentialPluginPrompt } from './CredentialPluginPrompt';
import { CredentialPluginSelected } from '.';

function CredentialPluginField(props) {
  const {
    children,
    id,
    name,
    label,
    validate,
    isRequired,
    isDisabled,
    i18n,
  } = props;
  const [showPluginWizard, setShowPluginWizard] = useState(false);
  const [field, meta, helpers] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);

  return (
    <FormGroup
      fieldId={id}
      helperTextInvalid={meta.error}
      isRequired={isRequired}
      isValid={isValid}
      label={label}
    >
      {field.value.credential ? (
        <CredentialPluginSelected
          credential={field.value.credential}
          onClearPlugin={() => helpers.setValue('')}
          onEditPlugin={() => setShowPluginWizard(true)}
        />
      ) : (
        <InputGroup>
          {React.cloneElement(children, {
            ...field,
            isRequired,
            onChange: (_, event) => {
              field.onChange(event);
            },
          })}
          <Tooltip
            content={i18n._(
              t`Populate field from an external secret management system`
            )}
          >
            <Button
              variant={ButtonVariant.control}
              aria-label={i18n._(
                t`Populate field from an external secret management system`
              )}
              onClick={() => setShowPluginWizard(true)}
              isDisabled={isDisabled}
            >
              <KeyIcon />
            </Button>
          </Tooltip>
        </InputGroup>
      )}
      {showPluginWizard && (
        <CredentialPluginPrompt
          initialValues={field.value}
          onClose={() => setShowPluginWizard(false)}
          onSubmit={val => {
            val.touched = true;
            helpers.setValue(val);
            setShowPluginWizard(false);
          }}
        />
      )}
    </FormGroup>
  );
}

CredentialPluginField.propTypes = {
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  validate: PropTypes.func,
  isRequired: PropTypes.bool,
  isDisabled: PropTypes.bool,
};

CredentialPluginField.defaultProps = {
  validate: () => {},
  isRequired: false,
  isDisabled: false,
};

export default withI18n()(CredentialPluginField);
