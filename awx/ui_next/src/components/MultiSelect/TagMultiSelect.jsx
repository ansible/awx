import React, { useState } from 'react';
import { func, string } from 'prop-types';
import { Select, SelectOption, SelectVariant } from '@patternfly/react-core';

function arrayToString(tags) {
  return tags.join(',');
}

function stringToArray(value) {
  return value.split(',').filter(val => !!val);
}

function TagMultiSelect({ onChange, value }) {
  const selections = stringToArray(value);
  const [options, setOptions] = useState(selections);
  const [isExpanded, setIsExpanded] = useState(false);

  const onSelect = (event, item) => {
    let newValue;
    if (selections.includes(item)) {
      newValue = selections.filter(i => i !== item);
    } else {
      newValue = selections.concat(item);
    }
    onChange(arrayToString(newValue));
  };

  const toggleExpanded = toggleValue => {
    setIsExpanded(toggleValue);
  };

  const renderOptions = opts => {
    return opts.map(option => (
      <SelectOption key={option} value={option}>
        {option}
      </SelectOption>
    ));
  };

  return (
    <Select
      variant={SelectVariant.typeaheadMulti}
      onToggle={toggleExpanded}
      onSelect={onSelect}
      onClear={() => onChange('')}
      onFilter={event => {
        const str = event.target.value.toLowerCase();
        const matches = options.filter(o => o.toLowerCase().includes(str));
        return renderOptions(matches);
      }}
      isCreatable
      onCreateOption={name => {
        name = name.trim();
        if (!options.includes(name)) {
          setOptions(options.concat(name));
        }
        return name;
      }}
      selections={selections}
      isExpanded={isExpanded}
      ariaLabelledBy="tag-select"
    >
      {renderOptions(options)}
    </Select>
  );
}

TagMultiSelect.propTypes = {
  onChange: func.isRequired,
  value: string.isRequired,
};

export default TagMultiSelect;
