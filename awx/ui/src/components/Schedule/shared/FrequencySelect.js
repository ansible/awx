import React, { useState } from 'react';
import { arrayOf, string } from 'prop-types';
import { Select, SelectOption, SelectVariant } from '@patternfly/react-core';

export default function FrequencySelect({
  id,
  value,
  onChange,
  onBlur,
  placeholderText,
  children,
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
    <Select
      variant={SelectVariant.checkbox}
      onSelect={onSelect}
      selections={value}
      placeholderText={placeholderText}
      onToggle={onToggle}
      isOpen={isOpen}
      ouiaId={`frequency-select-${id}`}
    >
      {children}
    </Select>
  );
}

FrequencySelect.propTypes = {
  value: arrayOf(string).isRequired,
};

export { SelectOption, SelectVariant };
