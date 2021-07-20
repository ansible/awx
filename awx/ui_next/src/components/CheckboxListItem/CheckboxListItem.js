import 'styled-components/macro';
import React from 'react';
import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { Td, Tr } from '@patternfly/react-table';

const CheckboxListItem = ({
  isRadio = false,
  isSelected = false,
  itemId,
  label,
  name,
  onDeselect,
  rowIndex,
  onSelect,
  columns,
  item,
}) => {
  const handleRowClick = () => {
    if (isSelected && !isRadio) {
      onDeselect(itemId);
    } else {
      onSelect(itemId);
    }
  };

  return (
    <Tr
      ouiaId={`list-item-${itemId}`}
      id={`list-item-${itemId}`}
      onClick={handleRowClick}
      css="cursor: default"
    >
      <Td
        id={`check-action-item-${itemId}`}
        select={{
          rowIndex,
          isSelected,
          variant: isRadio ? 'radio' : 'checkbox',
        }}
        name={name}
        dataLabel={t`Selected`}
      />

      {columns?.length > 0 ? (
        columns.map((col) => (
          <Td aria-label={col.name} dataLabel={col.key} key={col.key}>
            {item[col.key]}
          </Td>
        ))
      ) : (
        <Td aria-labelledby={itemId} dataLabel={label}>
          <b>{label}</b>
        </Td>
      )}
    </Tr>
  );
};

CheckboxListItem.propTypes = {
  isSelected: PropTypes.bool.isRequired,
  itemId: PropTypes.number.isRequired,
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  onDeselect: PropTypes.func.isRequired,
  onSelect: PropTypes.func.isRequired,
};

export default CheckboxListItem;
