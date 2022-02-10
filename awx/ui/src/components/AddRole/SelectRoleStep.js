import React from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';

import CheckboxCard from './CheckboxCard';
import { SelectedList } from '../SelectedList';

function RolesStep({
  onRolesClick,
  roles,
  selectedListKey,
  selectedListLabel,
  selectedResourceRows,
  selectedRoleRows,
}) {
  return (
    <>
      <div>
        {t`Choose roles to apply to the selected resources.  Note that all selected roles will be applied to all selected resources.`}
      </div>
      <div>
        {selectedResourceRows.length > 0 && (
          <SelectedList
            displayKey={selectedListKey}
            isReadOnly
            label={selectedListLabel || t`Selected`}
            selected={selectedResourceRows}
          />
        )}
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px 20px',
          marginTop: '20px',
        }}
      >
        {Object.keys(roles).map((role) => (
          <CheckboxCard
            description={roles[role].description}
            itemId={roles[role].id}
            isSelected={selectedRoleRows.some(
              (item) => item.id === roles[role].id
            )}
            key={roles[role].id}
            name={roles[role].name}
            onSelect={() => onRolesClick(roles[role])}
          />
        ))}
      </div>
    </>
  );
}

RolesStep.propTypes = {
  onRolesClick: PropTypes.func,
  roles: PropTypes.objectOf(PropTypes.object).isRequired,
  selectedListKey: PropTypes.string,
  selectedListLabel: PropTypes.string,
  selectedResourceRows: PropTypes.arrayOf(PropTypes.object),
  selectedRoleRows: PropTypes.arrayOf(PropTypes.object),
};

RolesStep.defaultProps = {
  onRolesClick: () => {},
  selectedListKey: 'name',
  selectedListLabel: null,
  selectedResourceRows: [],
  selectedRoleRows: [],
};

export default RolesStep;
