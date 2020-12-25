import React, { useState, useRef, useEffect, Fragment } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Dropdown, DropdownPosition } from '@patternfly/react-core';
import { ToolbarAddButton } from '../PaginatedDataList';
import { useKebabifiedMenu } from '../../contexts/Kebabified';

function AddDropDownButton({ dropdownItems, i18n }) {
  const { isKebabified } = useKebabifiedMenu();
  const [isOpen, setIsOpen] = useState(false);
  const element = useRef(null);

  useEffect(() => {
    const toggle = e => {
      if (!isKebabified && (!element || !element.current.contains(e.target))) {
        setIsOpen(false);
      }
    };

    document.addEventListener('click', toggle, false);
    return () => {
      document.removeEventListener('click', toggle);
    };
  }, [isKebabified]);

  if (isKebabified) {
    return <Fragment>{dropdownItems}</Fragment>;
  }

  return (
    <div ref={element} key="add">
      <Dropdown
        isPlain
        isOpen={isOpen}
        position={DropdownPosition.right}
        toggle={
          <ToolbarAddButton
            aria-label={i18n._(t`Add`)}
            showToggleIndicator
            onClick={() => setIsOpen(!isOpen)}
          />
        }
        dropdownItems={dropdownItems}
      />
    </div>
  );
}

AddDropDownButton.propTypes = {
  dropdownItems: PropTypes.arrayOf(PropTypes.element.isRequired).isRequired,
};

export { AddDropDownButton as _AddDropDownButton };
export default withI18n()(AddDropDownButton);
