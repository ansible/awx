import React from 'react';
import {
  arrayOf,
  oneOfType,
  func,
  number,
  string,
  shape,
  bool,
} from 'prop-types';

import { t } from '@lingui/macro';
import { FormSelect, FormSelectOption } from '@patternfly/react-core';

function AnsibleSelect({
  id,
  data,
  isValid,
  onBlur,
  value,
  className,
  isDisabled,
  onChange,
  name,
}) {
  const onSelectChange = (val, event) => {
    event.target.name = name;
    onChange(event, val);
  };

  return (
    <FormSelect
      id={id}
      ouiaId={id}
      value={value}
      onChange={onSelectChange}
      onBlur={onBlur}
      aria-label={t`Select Input`}
      validated={isValid ? 'default' : 'error'}
      className={className}
      isDisabled={isDisabled}
    >
      {data.map((option) => (
        <FormSelectOption
          key={option.key}
          value={option.value}
          label={option.label}
          isDisabled={option.isDisabled}
        >
          {option.label}
        </FormSelectOption>
      ))}
    </FormSelect>
  );
}

const Option = shape({
  key: oneOfType([string, number]).isRequired,
  value: oneOfType([string, number]).isRequired,
  label: string.isRequired,
  isDisabled: bool,
});

AnsibleSelect.defaultProps = {
  data: [],
  isValid: true,
  onBlur: () => {},
  className: '',
  isDisabled: false,
};

AnsibleSelect.propTypes = {
  data: arrayOf(Option),
  id: string.isRequired,
  isValid: bool,
  onBlur: func,
  onChange: func.isRequired,
  value: oneOfType([string, number]).isRequired,
  className: string,
  isDisabled: bool,
};

export { AnsibleSelect as _AnsibleSelect };
export default AnsibleSelect;
