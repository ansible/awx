import React, { useState, useRef, useEffect, Fragment } from 'react';
import { func, string, arrayOf, shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Dropdown,
  DropdownItem,
  DropdownPosition,
  DropdownToggle,
} from '@patternfly/react-core';
import { useKebabifiedMenu } from '../../../contexts/Kebabified';

function AddDropdown({ dropdownItems, i18n }) {
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
    return (
      <Fragment>
        {dropdownItems.map(item => (
          <DropdownItem
            key={item.key}
            aria-label={item.title}
            onClick={item.onAdd}
          >
            {item.title}
          </DropdownItem>
        ))}
      </Fragment>
    );
  }

  return (
    <div ref={element} key="add">
      <Dropdown
        isOpen={isOpen}
        position={DropdownPosition.right}
        toggle={
          <DropdownToggle
            id="add"
            aria-label="add"
            isPrimary
            onToggle={() => setIsOpen(prevState => !prevState)}
          >
            {i18n._(t`Add`)}
          </DropdownToggle>
        }
        dropdownItems={dropdownItems.map(item => (
          <DropdownItem
            className="pf-c-dropdown__menu-item"
            key={item.key}
            aria-label={item.title}
            onClick={item.onAdd}
          >
            {item.title}
          </DropdownItem>
        ))}
      />
    </div>
  );
}

AddDropdown.propTypes = {
  dropdownItems: arrayOf(
    shape({
      label: string.isRequired,
      onAdd: func.isRequired,
      key: string.isRequired,
    })
  ).isRequired,
};

export { AddDropdown as _AddDropdown };
export default withI18n()(AddDropdown);
