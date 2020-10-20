import React from 'react';
import { string, func, node } from 'prop-types';
import { useField } from 'formik';
import { Checkbox } from '@patternfly/react-core';
import Popover from '../Popover';

function CheckboxField({
  id,
  name,
  label,
  tooltip,
  validate,
  isDisabled,
  ...rest
}) {
  const [field] = useField({ name, validate });
  return (
    <Checkbox
      isDisabled={isDisabled}
      aria-label={label}
      label={
        <span>
          {label}
          &nbsp;
          {tooltip && <Popover content={tooltip} />}
        </span>
      }
      id={id}
      {...rest}
      isChecked={field.value}
      {...field}
      onChange={(value, event) => {
        field.onChange(event);
      }}
    />
  );
}
CheckboxField.propTypes = {
  id: string.isRequired,
  name: string.isRequired,
  label: string.isRequired,
  validate: func,
  tooltip: node,
};
CheckboxField.defaultProps = {
  validate: () => {},
  tooltip: '',
};

export default CheckboxField;
