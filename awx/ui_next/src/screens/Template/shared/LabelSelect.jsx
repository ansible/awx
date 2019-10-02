import React, { useState, useEffect } from 'react';
import { func, arrayOf, number, shape, string, oneOfType } from 'prop-types';
import MultiSelect from '@components/MultiSelect';
import { LabelsAPI } from '@api';

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
      labels = labels.concat(results);
    }
    setLabels(labels);
  } catch (err) {
    onError(err);
  }
}

function LabelSelect({ value, onChange, onError }) {
  const [options, setOptions] = useState([]);
  useEffect(() => {
    loadLabelOptions(setOptions, onError);
  }, []);

  return (
    <MultiSelect
      onChange={onChange}
      value={value}
      options={options}
      createNewItem={name => ({
        id: name,
        name,
        isNew: true,
      })}
    />
  );
}
LabelSelect.propTypes = {
  value: arrayOf(
    shape({
      id: oneOfType([number, string]).isRequired,
      name: string.isRequired,
    })
  ).isRequired,
  onError: func.isRequired,
};

export default LabelSelect;
