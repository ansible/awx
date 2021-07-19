import React from 'react';
import PropTypes from 'prop-types';
import { useField } from 'formik';
import { FormGroup, TextArea } from '@patternfly/react-core';
import Popover from '../Popover';

function ArrayTextField(props) {
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

  const [field, meta, helpers] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);
  const value = field.value || [];

  return (
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
        value={value.join('\n')}
        onChange={val => {
          helpers.setValue(val.split('\n').map(v => v.trim()));
        }}
      />
    </FormGroup>
  );
}

ArrayTextField.propTypes = {
  helperText: PropTypes.string,
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.oneOfType([PropTypes.object, PropTypes.string]).isRequired,
  validate: PropTypes.func,
  isRequired: PropTypes.bool,
  tooltip: PropTypes.node,
  tooltipMaxWidth: PropTypes.string,
};

ArrayTextField.defaultProps = {
  helperText: '',
  validate: () => {},
  isRequired: false,
  tooltip: null,
  tooltipMaxWidth: '',
};

export default ArrayTextField;
