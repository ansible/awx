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
  TextInput,
  Tooltip,
} from '@patternfly/react-core';
import { EyeIcon, EyeSlashIcon } from '@patternfly/react-icons';

function PasswordField(props) {
  const { id, name, label, validate, isRequired, i18n } = props;
  const [inputType, setInputType] = useState('password');
  const [field, meta] = useField({ name, validate });

  const isValid = !(meta.touched && meta.error);

  const handlePasswordToggle = () => {
    setInputType(inputType === 'text' ? 'password' : 'text');
  };

  return (
    <FormGroup
      fieldId={id}
      helperTextInvalid={meta.error}
      isRequired={isRequired}
      isValid={isValid}
      label={label}
    >
      <InputGroup>
        <Tooltip
          content={inputType === 'password' ? i18n._(t`Show`) : i18n._(t`Hide`)}
        >
          <Button
            variant={ButtonVariant.control}
            aria-label={i18n._(t`Toggle Password`)}
            onClick={handlePasswordToggle}
          >
            {inputType === 'password' && <EyeSlashIcon />}
            {inputType === 'text' && <EyeIcon />}
          </Button>
        </Tooltip>
        <TextInput
          id={id}
          placeholder={field.value === '$encrypted$' ? 'ENCRYPTED' : undefined}
          {...field}
          value={field.value === '$encrypted$' ? '' : field.value}
          isRequired={isRequired}
          isValid={isValid}
          type={inputType}
          onChange={(_, event) => {
            field.onChange(event);
          }}
        />
      </InputGroup>
    </FormGroup>
  );
}

PasswordField.propTypes = {
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  validate: PropTypes.func,
  isRequired: PropTypes.bool,
};

PasswordField.defaultProps = {
  validate: () => {},
  isRequired: false,
};

export default withI18n()(PasswordField);
