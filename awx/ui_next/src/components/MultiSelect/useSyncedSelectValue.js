import { useState, useEffect } from 'react';

/*
  Hook for using PatternFly's <Select> component when a pre-existing value
  is loaded from somewhere other than the options. Guarantees object equality
  between objects in `value` and the corresponding objects loaded as
  `options` (based on matched id value).
 */
export default function useSyncedSelectValue(value, onChange) {
  const [options, setOptions] = useState([]);
  const [selections, setSelections] = useState([]);

  useEffect(() => {
    const newOptions = [];
    if (value !== selections && options.length) {
      const syncedValue = value.map(item => {
        const match = options.find(i => {
          return i.id === item.id;
        });
        if (!match) {
          newOptions.push(item);
        }
        return match || item;
      });
      setSelections(syncedValue);
    }
    if (newOptions.length > 0) {
      setOptions(options.concat(newOptions));
    }
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, [value, options]);

  const onSelect = (event, item) => {
    if (selections.includes(item)) {
      onChange(selections.filter(i => i !== item));
    } else {
      onChange(selections.concat(item));
    }
  };
  return {
    selections: options.length ? addToStringToObjects(selections) : [],
    onSelect,
    options,
    setOptions: newOpts => setOptions(addToStringToObjects(newOpts)),
  };
}

/*
  PF uses toString to generate React keys. This is used to ensure
  all objects in the array have a toString method.
 */
function addToStringToObjects(items = []) {
  items.forEach(item => {
    item.toString = toString;
  });
  return items;
}

function toString() {
  return String(this.id);
}
