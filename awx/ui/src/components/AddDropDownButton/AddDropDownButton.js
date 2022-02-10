/* eslint-disable react/jsx-no-useless-fragment */
import React, { useState, useRef, useEffect } from 'react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Dropdown, DropdownPosition } from '@patternfly/react-core';
import { useKebabifiedMenu } from 'contexts/Kebabified';
import { ToolbarAddButton } from '../PaginatedTable';

function AddDropDownButton({ dropdownItems, ouiaId }) {
  const { isKebabified } = useKebabifiedMenu();
  const [isOpen, setIsOpen] = useState(false);
  const element = useRef(null);

  useEffect(() => {
    const toggle = (e) => {
      if (!isKebabified && (!element || !element.current?.contains(e.target))) {
        setIsOpen(false);
      }
    };

    document.addEventListener('click', toggle, false);
    return () => {
      document.removeEventListener('click', toggle);
    };
  }, [isKebabified]);

  if (isKebabified) {
    return <>{dropdownItems}</>;
  }

  return (
    <div ref={element} key="add">
      <Dropdown
        isPlain
        isOpen={isOpen}
        position={DropdownPosition.right}
        toggle={
          <ToolbarAddButton
            ouiaId={ouiaId}
            aria-label={t`Add`}
            showToggleIndicator
            onClick={() => setIsOpen(!isOpen)}
          />
        }
        dropdownItems={dropdownItems}
        ouiaId="add-dropdown"
      />
    </div>
  );
}

AddDropDownButton.propTypes = {
  dropdownItems: PropTypes.arrayOf(PropTypes.element.isRequired).isRequired,
};

export { AddDropDownButton as _AddDropDownButton };
export default AddDropDownButton;
