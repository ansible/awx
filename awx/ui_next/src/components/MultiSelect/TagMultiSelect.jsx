import React, { useState } from 'react';
import { func, string } from 'prop-types';
import { Select, SelectOption, SelectVariant } from '@patternfly/react-core';
import usePFSelect from '@components/MultiSelect/usePFSelect';

function arrayToString(tags) {
  return tags.map(v => v.name).join(',');
}

function stringToArray(value) {
  return value
    .split(',')
    .filter(val => !!val)
    .map(val => ({
      id: val,
      name: val,
    }));
}

/*
 * Adapter providing a simplified API to a MultiSelect. The value
 * is a comma-separated string.
 */
function TagMultiSelect({ onChange, value }) {
  const { selections, onSelect, options, setOptions } = usePFSelect(
    value, // TODO: convert with stringToArray without triggering re-render loop
    val => onChange(arrayToString(val))
  );
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const renderOptions = opts => {
    return opts.map(option => (
      <SelectOption key={option.id} value={option}>
        {option.name}
      </SelectOption>
    ));
  };

  return (
    <Select
      variant={SelectVariant.typeaheadMulti}
      onToggle={toggleExpanded}
      onSelect={onSelect}
      onClear={() => onChange([])}
      onFilter={event => {
        const str = event.target.value.toLowerCase();
        const matches = options.filter(o => o.name.toLowerCase().includes(str));
        return renderOptions(matches);
      }}
      isCreatable
      onCreateOption={name => {
        // TODO check for duplicate in options
        const newItem = { id: name, name };
        setOptions(options.concat(newItem));
        return newItem;
      }}
      selections={selections}
      isExpanded={isExpanded}
      ariaLabelledBy="tag-select"
    >
      {renderOptions(options)}
    </Select>
  );
  //
  // return (
  //   <MultiSelect
  //     onChange={val => {
  //       onChange(arrayToString(val));
  //     }}
  //     onAddNewItem={newItem => {
  //       if (!options.find(o => o.name === newItem.name)) {
  //         setOptions(options.concat(newItem));
  //       }
  //     }}
  //     value={stringToArray(value)}
  //     options={options}
  //     createNewItem={name => ({ id: name, name })}
  //   />
  // );
}

TagMultiSelect.propTypes = {
  onChange: func.isRequired,
  value: string.isRequired,
};

export default TagMultiSelect;
