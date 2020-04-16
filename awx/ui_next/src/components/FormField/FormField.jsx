import React from 'react';
import PropTypes from 'prop-types';
import { useField } from 'formik';
import { FormGroup, TextInput, TextArea } from '@patternfly/react-core';
import FieldTooltip from './FieldTooltip';

function FormField(props) {
  const {
    id,
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
          helperTextInvalid={meta.error}
          isRequired={isRequired}
          isValid={isValid}
          label={label}
        >
          <FieldTooltip content={tooltip} maxWidth={tooltipMaxWidth} />
          <TextArea
            id={id}
            isRequired={isRequired}
            isValid={isValid}
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
          helperTextInvalid={meta.error}
          isRequired={isRequired}
          isValid={isValid}
          label={label}
        >
          <FieldTooltip content={tooltip} maxWidth={tooltipMaxWidth} />
          <TextInput
            id={id}
            isRequired={isRequired}
            isValid={isValid}
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
  type: 'text',
  validate: () => {},
  isRequired: false,
  tooltip: null,
  tooltipMaxWidth: '',
};

export default FormField;
