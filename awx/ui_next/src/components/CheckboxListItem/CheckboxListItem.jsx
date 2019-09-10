import React from 'react';
import PropTypes from 'prop-types';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCell,
} from '@patternfly/react-core';
import DataListCheck from '@components/DataListCheck';
import DataListRadio from '@components/DataListRadio';
import VerticalSeparator from '../VerticalSeparator';

const CheckboxListItem = ({
  itemId,
  name,
  label,
  isSelected,
  onSelect,
  isRadio,
}) => {
  const CheckboxRadio = isRadio ? DataListRadio : DataListCheck;
  return (
    <DataListItem key={itemId} aria-labelledby={`check-action-item-${itemId}`}>
      <DataListItemRow>
        <CheckboxRadio
          id={`selected-${itemId}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={`check-action-item-${itemId}`}
          name={name}
          value={itemId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell
              key="divider"
              className="pf-c-data-list__cell--divider"
            >
              <VerticalSeparator />
            </DataListCell>,
            <DataListCell key="name">
              <label
                id={`check-action-item-${itemId}`}
                htmlFor={`selected-${itemId}`}
                className="check-action-item"
              >
                <b>{label}</b>
              </label>
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
};

CheckboxListItem.propTypes = {
  itemId: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  isSelected: PropTypes.bool.isRequired,
  onSelect: PropTypes.func.isRequired,
};

export default CheckboxListItem;
