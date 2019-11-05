import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Field } from 'formik';
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

  const handlePasswordToggle = () => {
    setInputType(inputType === 'text' ? 'password' : 'text');
  };

  return (
    <Field
      name={name}
      validate={validate}
      render={({ field, form }) => {
        const isValid =
          form && (!form.touched[field.name] || !form.errors[field.name]);
        return (
          <FormGroup
            fieldId={id}
            helperTextInvalid={form.errors[field.name]}
            isRequired={isRequired}
            isValid={isValid}
            label={label}
          >
            <InputGroup>
              <Tooltip
                content={
                  inputType === 'password' ? i18n._(t`Show`) : i18n._(t`Hide`)
                }
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
                isRequired={isRequired}
                isValid={isValid}
                type={inputType}
                {...field}
                onChange={(value, event) => {
                  field.onChange(event);
                }}
              />
            </InputGroup>
          </FormGroup>
        );
      }}
    />
  );
}

PasswordField.propTypes = {
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  type: PropTypes.string,
  validate: PropTypes.func,
  isRequired: PropTypes.bool,
  tooltip: PropTypes.node,
  tooltipMaxWidth: PropTypes.string,
};

PasswordField.defaultProps = {
  type: 'text',
  validate: () => {},
  isRequired: false,
  tooltip: null,
  tooltipMaxWidth: '',
};

export default withI18n()(PasswordField);
