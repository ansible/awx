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
  initialValues,
  onNewLabelsChange,
  onRemovedLabelsChange,
  onError,
}) {
  const [options, setOptions] = useState([]);
  // TODO: move newLabels into a prop?
  const [newLabels, setNewLabels] = useState([]);
  const [removedLabels, setRemovedLabels] = useState([]);
  useEffect(() => {
    loadLabelOptions(setOptions, onError);
  }, []);

  const handleNewLabel = label => {
    const isIncluded = newLabels.some(l => l.name === label.name);
    if (isIncluded) {
      const filteredLabels = newLabels.filter(
        newLabel => newLabel.name !== label
      );
      setNewLabels(filteredLabels);
    } else {
      const updatedNewLabels = newLabels.concat({
        name: label.name,
        associate: true,
        id: label.id,
        // TODO: can this be null? what happens if inventory > org id changes?
        // organization: organizationId,
      });
      setNewLabels(updatedNewLabels);
      onNewLabelsChange(updatedNewLabels);
    }
  };

  const handleRemoveLabel = label => {
    const isAssociatedLabel = initialValues.some(
      l => l.id === label.id
    );
    if (isAssociatedLabel) {
      const updatedRemovedLabels = removedLabels.concat({
        id: label.id,
        disassociate: true,
      });
      setRemovedLabels(updatedRemovedLabels);
      onRemovedLabelsChange(updatedRemovedLabels);
    } else {
      const filteredLabels = newLabels.filter(l => l.name !== label.name);
      setNewLabels(filteredLabels);
      onNewLabelsChange(filteredLabels);
    }
  };

  return (
    <MultiSelect
      onAddNewItem={handleNewLabel}
      onRemoveItem={handleRemoveLabel}
      associatedItems={initialValues}
      options={options}
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
  onNewLabelsChange: func.isRequired,
  onRemovedLabelsChange: func.isRequired,
  onError: func.isRequired,
};

export default LabelSelect;
