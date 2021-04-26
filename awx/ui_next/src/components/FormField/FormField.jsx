import React from 'react';
import PropTypes from 'prop-types';
import { useField } from 'formik';
import { FormGroup, TextInput, TextArea } from '@patternfly/react-core';
import Popover from '../Popover';

function FormField(props) {
  const {
    id,
    helperText,
    name,
    label,
    tooltip,
    tooltipMaxWidth,
    validate,
    isRequired,
    type,
    ...rest
  } = props;

  const [field, meta] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);

  return (
    <>
      {(type === 'textarea' && (
        <FormGroup
          fieldId={id}
          helperText={helperText}
          helperTextInvalid={meta.error}
          isRequired={isRequired}
          validated={isValid ? 'default' : 'error'}
          label={label}
          labelIcon={<Popover content={tooltip} maxWidth={tooltipMaxWidth} />}
        >
          <TextArea
            id={id}
            isRequired={isRequired}
            validated={isValid ? 'default' : 'error'}
            resizeOrientation="vertical"
            {...rest}
            {...field}
            onChange={(value, event) => {
              field.onChange(event);
            }}
          />
        </FormGroup>
      )) || (
        <FormGroup
          fieldId={id}
          helperText={helperText}
          helperTextInvalid={meta.error}
          isRequired={isRequired}
          validated={isValid ? 'default' : 'error'}
          label={label}
          labelIcon={<Popover content={tooltip} maxWidth={tooltipMaxWidth} />}
        >
          <TextInput
            id={id}
            isRequired={isRequired}
            validated={isValid ? 'default' : 'error'}
            {...rest}
            {...field}
            type={type}
            onChange={(value, event) => {
              field.onChange(event);
            }}
          />
        </FormGroup>
      )}
    </>
  );
}

FormField.propTypes = {
  helperText: PropTypes.string,
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.oneOfType([PropTypes.object, PropTypes.string]).isRequired,
  type: PropTypes.string,
  validate: PropTypes.func,
  isRequired: PropTypes.bool,
  tooltip: PropTypes.node,
  tooltipMaxWidth: PropTypes.string,
};

FormField.defaultProps = {
  helperText: '',
  type: 'text',
  validate: () => {},
  isRequired: false,
  tooltip: null,
  tooltipMaxWidth: '',
};

export default FormField;
