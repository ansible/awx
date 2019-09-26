import React, { useState, useEffect } from 'react';
import { func, arrayOf, number, shape, string } from 'prop-types';
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

function LabelSelect({
  initialValues, // todo: change to value, controlled ?
  onChange,
  onError,
}) {
  const [options, setOptions] = useState([]);
  // TODO: move newLabels into a prop?
  useEffect(() => {
    loadLabelOptions(setOptions, onError);
  }, []);

  return (
    <MultiSelect
      onChange={onChange}
      associatedItems={initialValues}
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
  initialValues: arrayOf(
    shape({
      id: number.isRequired,
      name: string.isRequired,
    })
  ).isRequired,
  onError: func.isRequired,
};

export default LabelSelect;
