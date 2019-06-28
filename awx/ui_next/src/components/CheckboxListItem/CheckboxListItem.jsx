import React from 'react';
import PropTypes from 'prop-types';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCheck,
  DataListCell,
} from '@patternfly/react-core';

import VerticalSeparator from '../VerticalSeparator';

const CheckboxListItem = ({ itemId, name, isSelected, onSelect }) => (
  <DataListItem key={itemId} aria-labelledby={`check-action-item-${itemId}`}>
    <DataListItemRow>
      <DataListCheck
        id={`selected-${itemId}`}
        checked={isSelected}
        onChange={onSelect}
        aria-labelledby={`check-action-item-${itemId}`}
        value={itemId}
      />
      <DataListItemCells
        dataListCells={[
          <DataListCell key="divider" className="pf-c-data-list__cell--divider">
            <VerticalSeparator />
          </DataListCell>,
          <DataListCell key="name">
            <label
              id={`check-action-item-${itemId}`}
              htmlFor={`selected-${itemId}`}
              className="check-action-item"
            >
              <b>{name}</b>
            </label>
          </DataListCell>,
        ]}
      />
    </DataListItemRow>
  </DataListItem>
);

CheckboxListItem.propTypes = {
  itemId: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  isSelected: PropTypes.bool.isRequired,
  onSelect: PropTypes.func.isRequired,
};

export default CheckboxListItem;
