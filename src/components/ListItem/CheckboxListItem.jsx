import React from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Checkbox,
} from '@patternfly/react-core';

const CheckboxListItem = ({
  itemId,
  name,
  isSelected,
  onSelect,
}) => (
  <li key={itemId} className="pf-c-data-list__item" aria-labelledby="check-action-item1">
    <div className="pf-c-data-list__check">
      <I18n>
        {({ i18n }) => (
          <Checkbox
            checked={isSelected}
            onChange={onSelect}
            aria-label={i18n._(t`selected ${itemId}`)}
            id={`selectd-${itemId}`}
            value={itemId}
          />
        )}
      </I18n>
    </div>
    <div className="pf-c-data-list__cell">
      <label htmlFor={`selectd-${itemId}`} className="check-action-item">
        <b>{name}</b>
      </label>
    </div>
  </li>
);

CheckboxListItem.propTypes = {
  itemId: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  isSelected: PropTypes.bool.isRequired,
  onSelect: PropTypes.func.isRequired,
};

export default CheckboxListItem;
