import React from 'react';
import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { Td, Tr } from '@patternfly/react-table';

const CheckboxListItem = ({
  isDisabled = false,
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
  return (
    <Tr ouiaId={`list-item-${itemId}`} id={`list-item-${itemId}`}>
      <Td
        id={`check-action-item-${itemId}`}
        select={{
          rowIndex,
          isSelected,
          onSelect: isSelected ? onDeselect : onSelect,
          disable: isDisabled,
          variant: isRadio ? 'radio' : 'checkbox',
        }}
        name={name}
        dataLabel={t`Selected`}
      />

      {columns?.length > 0 ? (
        columns.map(col => (
          <Td aria-label={col.name} dataLabel={col.key}>
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
