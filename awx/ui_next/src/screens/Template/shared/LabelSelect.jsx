import React, { useState, useEffect } from 'react';
import { func, arrayOf, number, shape, string, oneOfType } from 'prop-types';
import { Select, SelectOption, SelectVariant } from '@patternfly/react-core';
import { LabelsAPI } from '../../../api';
import { useSyncedSelectValue } from '../../../components/MultiSelect';

async function loadLabelOptions(setLabels, onError) {
  let labels;
  try {
    const { data } = await LabelsAPI.read({
      page: 1,
      page_size: 200,
      order_by: 'name',
    });
    labels = data.results;
    setLabels(labels);
    if (data.next && data.next.includes('page=2')) {
      const {
        data: { results },
      } = await LabelsAPI.read({
        page: 2,
        page_size: 200,
        order_by: 'name',
      });
      setLabels(labels.concat(results));
    }
  } catch (err) {
    onError(err);
  }
}

function LabelSelect({ value, placeholder, onChange, onError, createText }) {
  const [isLoading, setIsLoading] = useState(true);
  const { selections, onSelect, options, setOptions } = useSyncedSelectValue(
    value,
    onChange
  );
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpanded = toggleValue => {
    setIsExpanded(toggleValue);
  };

  useEffect(() => {
    (async () => {
      await loadLabelOptions(setOptions, onError);
      setIsLoading(false);
    })();
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, []);

  const renderOptions = opts => {
    return opts.map(option => (
      <SelectOption key={option.id} aria-label={option.name} value={option}>
        {option.name}
      </SelectOption>
    ));
  };

  return (
    <Select
      variant={SelectVariant.typeaheadMulti}
      onToggle={toggleExpanded}
      onSelect={(e, item) => {
        if (typeof item === 'string') {
          item = { id: item, name: item };
        }
        onSelect(e, item);
      }}
      onClear={() => onChange([])}
      onFilter={event => {
        const str = event.target.value.toLowerCase();
        const matches = options.filter(o => o.name.toLowerCase().includes(str));
        return renderOptions(matches);
      }}
      isCreatable
      onCreateOption={label => {
        label = label.trim();
        if (!options.includes(label)) {
          setOptions(options.concat({ name: label, id: label }));
        }
        return label;
      }}
      isDisabled={isLoading}
      selections={selections}
      isOpen={isExpanded}
      aria-labelledby="label-select"
      placeholderText={placeholder}
      createText={createText}
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
