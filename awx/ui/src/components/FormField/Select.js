import React, { useState } from 'react';
import { arrayOf, oneOf, string } from 'prop-types';
import {
  Select as PFSelect,
  SelectOption,
  SelectVariant,
} from '@patternfly/react-core';

export default function Select({
  value,
  onChange,
  onBlur,
  placeholderText,
  children,
  variant,
}) {
  const [isOpen, setIsOpen] = useState(false);

  const onSelect = (event, selectedValue) => {
    if (selectedValue === 'none') {
      onChange([]);
      setIsOpen(false);
      return;
    }
    const index = value.indexOf(selectedValue);
    if (index === -1) {
      onChange(value.concat(selectedValue));
    } else {
      onChange(value.slice(0, index).concat(value.slice(index + 1)));
    }
  };

  const onToggle = (val) => {
    if (!val) {
      onBlur();
    }
    setIsOpen(val);
  };

  return (
    <PFSelect
      variant={variant}
      onSelect={onSelect}
      selections={value}
      placeholderText={placeholderText}
      onToggle={onToggle}
      isOpen={isOpen}
    >
      {children}
    </PFSelect>
  );
}

Select.propTypes = {
  variant: oneOf(Object.values(SelectVariant)),
  value: arrayOf(string).isRequired,
};

Select.defaultProps = {
  variant: SelectVariant.single,
};

export { SelectOption, SelectVariant };
