import React, { useState } from 'react';
import { func, string } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Dropdown,
  DropdownItem,
  DropdownPosition,
  DropdownToggle,
} from '@patternfly/react-core';

function AddDropdown({
  i18n,
  onAddNew,
  onAddExisting,
  newTitle,
  existingTitle,
  label,
}) {
  const [isOpen, setIsOpen] = useState(false);

  const dropdownItems = [
    <DropdownItem
      key="add-new"
      aria-label={`add new ${label}`}
      component="button"
      onClick={onAddNew}
    >
      {newTitle}
    </DropdownItem>,
    <DropdownItem
      key="add-existing"
      aria-label={`add existing ${label}`}
      component="button"
      onClick={onAddExisting}
    >
      {existingTitle}
    </DropdownItem>,
  ];

  return (
    <Dropdown
      isOpen={isOpen}
      position={DropdownPosition.right}
      toggle={
        <DropdownToggle
          id={`add-${label}-dropdown`}
          aria-label={`add ${label}`}
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

AddDropdown.propTypes = {
  onAddNew: func.isRequired,
  onAddExisting: func.isRequired,
  newTitle: string.isRequired,
  existingTitle: string.isRequired,
  label: string.isRequired,
};

export default withI18n()(AddDropdown);
