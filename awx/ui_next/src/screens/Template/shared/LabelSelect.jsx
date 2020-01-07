import React, { useState, useEffect } from 'react';
import { func, arrayOf, number, shape, string, oneOfType } from 'prop-types';
import { Select, SelectOption, SelectVariant } from '@patternfly/react-core';
import { LabelsAPI } from '@api';

function setToString(labels) {
  labels.forEach(label => {
    label.toString = function toString() {
      return this.id;
    };
  });
  return labels;
}

async function loadLabelOptions(setLabels, onError) {
  let labels;
  try {
    const { data } = await LabelsAPI.read({
      page: 1,
      page_size: 200,
      order_by: 'name',
    });
    labels = setToString(data.results);
    setLabels(labels);
    if (data.next && data.next.includes('page=2')) {
      const {
        data: { results },
      } = await LabelsAPI.read({
        page: 2,
        page_size: 200,
        order_by: 'name',
      });
      setLabels(labels.concat(setToString(results)));
    }
  } catch (err) {
    onError(err);
  }
}

function LabelSelect({ value, placeholder, onChange, onError }) {
  const [options, setOptions] = useState([]);
  const [currentValue, setCurrentValue] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const handleSelect = (event, item) => {
    if (currentValue.includes(item)) {
      onChange(currentValue.filter(i => i.id !== item.id));
    } else {
      onChange(currentValue.concat(item));
    }
  };

  useEffect(() => {
    loadLabelOptions(setOptions, onError);
  }, [onError]);

  useEffect(() => {
    if (value !== currentValue && options.length) {
      const syncedValue = value.map(item =>
        options.find(i => i.id === item.id)
      );
      setCurrentValue(syncedValue);
    }
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, [value, options]);

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
      aria-label="Select a state"
      onToggle={toggleExpanded}
      onSelect={handleSelect}
      onClear={() => onChange([])}
      onFilter={event => {
        const str = event.target.value.toLowerCase();
        const matches = options.filter(o => o.name.toLowerCase().includes(str));
        return renderOptions(matches);
      }}
      selections={options.length ? setToString(currentValue) : []}
      isExpanded={isExpanded}
      ariaLabelledBy="label-select"
      placeholderText={placeholder}
    >
      {renderOptions(options)}
    </Select>
  );
}
LabelSelect.propTypes = {
  value: arrayOf(
    shape({
      id: oneOfType([number, string]).isRequired,
      name: string.isRequired,
    })
  ).isRequired,
  placeholder: string,
  onChange: func.isRequired,
  onError: func.isRequired,
};
LabelSelect.defaultProps = {
  placeholder: '',
};

export default LabelSelect;
