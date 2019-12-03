import React, { useState } from 'react';
import { func, string } from 'prop-types';
import MultiSelect from './MultiSelect';

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
  const [options, setOptions] = useState(stringToArray(value));

  return (
    <MultiSelect
      onChange={val => {
        onChange(arrayToString(val));
      }}
      onAddNewItem={newItem => {
        if (!options.find(o => o.name === newItem.name)) {
          setOptions(options.concat(newItem));
        }
      }}
      value={stringToArray(value)}
      options={options}
      createNewItem={name => ({ id: name, name })}
    />
  );
}

TagMultiSelect.propTypes = {
  onChange: func.isRequired,
  value: string.isRequired,
};

export default TagMultiSelect;
