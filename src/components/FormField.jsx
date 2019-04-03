import React from 'react';
import PropTypes from 'prop-types';
import { Field } from 'formik';
import { FormGroup, TextInput } from '@patternfly/react-core';

function FormField (props) {
  const { id, name, label, validate, isRequired, ...rest } = props;

  return (
    <Field
      name={name}
      validate={validate}
      render={({ field, form }) => {
        const isValid = !form.touched[field.name] || !form.errors[field.name];

        return (
          <FormGroup
            fieldId={id}
            helperTextInvalid={form.errors[field.name]}
            isRequired={isRequired}
            isValid={isValid}
            label={label}
          >
            <TextInput
              id={id}
              isRequired={isRequired}
              isValid={isValid}
              {...rest}
              {...field}
              onChange={(value, event) => {
                field.onChange(event);
              }}
            />
          </FormGroup>
        );
      }}
    />
  );
}

FormField.propTypes = {
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  type: PropTypes.string,
  validate: PropTypes.func,
  isRequired: PropTypes.bool,
};

FormField.defaultProps = {
  type: 'text',
  validate: () => {},
  isRequired: false,
};

export default FormField;
