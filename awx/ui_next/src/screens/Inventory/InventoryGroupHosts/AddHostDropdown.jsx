import React, { useState } from 'react';
import { func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Dropdown,
  DropdownItem,
  DropdownPosition,
  DropdownToggle,
} from '@patternfly/react-core';

function AddHostDropdown({ i18n, onAddNew, onAddExisting }) {
  const [isOpen, setIsOpen] = useState(false);

  const dropdownItems = [
    <DropdownItem
      key="add-new"
      aria-label="add new host"
      component="button"
      onClick={onAddNew}
    >
      {i18n._(t`Add New Host`)}
    </DropdownItem>,
    <DropdownItem
      key="add-existing"
      aria-label="add existing host"
      component="button"
      onClick={onAddExisting}
    >
      {i18n._(t`Add Existing Host`)}
    </DropdownItem>,
  ];

  return (
    <Dropdown
      isOpen={isOpen}
      position={DropdownPosition.right}
      toggle={
        <DropdownToggle
          id="add-host-dropdown"
          aria-label="add host"
          isPrimary
          onToggle={() => setIsOpen(prevState => !prevState)}
        >
          {i18n._(t`Add`)}
        </DropdownToggle>
      }
      dropdownItems={dropdownItems}
    />
  );
}

AddHostDropdown.propTypes = {
  onAddNew: func.isRequired,
  onAddExisting: func.isRequired,
};

export default withI18n()(AddHostDropdown);
