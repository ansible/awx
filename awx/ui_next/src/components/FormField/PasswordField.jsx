import React from 'react';
import PropTypes from 'prop-types';
import { useField } from 'formik';
import { FormGroup, InputGroup } from '@patternfly/react-core';
import PasswordInput from './PasswordInput';

function PasswordField(props) {
  const { id, name, label, validate, isRequired } = props;
  const [, meta] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);

  return (
    <FormGroup
      fieldId={id}
      helperTextInvalid={meta.error}
      isRequired={isRequired}
      validated={(isValid) ? 'default' : 'error'}
      label={label}
    >
      <InputGroup>
        <PasswordInput {...props} />
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
  isDisabled: PropTypes.bool,
};

PasswordField.defaultProps = {
  validate: () => {},
  isRequired: false,
  isDisabled: false,
};

export default PasswordField;
