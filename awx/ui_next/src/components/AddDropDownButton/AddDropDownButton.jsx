import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';
import { Dropdown, DropdownPosition } from '@patternfly/react-core';
import { ToolbarAddButton } from '@components/PaginatedDataList';

function AddDropDownButton({ dropdownItems }) {
  const [isOpen, setIsOpen] = useState(false);
  const element = useRef(null);

  const toggle = e => {
    if (!element || !element.current.contains(e.target)) {
      setIsOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('click', toggle, false);
    return () => {
      document.removeEventListener('click', toggle);
    };
  }, []);

  return (
    <div ref={element} key="add">
      <Dropdown
        isPlain
        isOpen={isOpen}
        position={DropdownPosition.right}
        toggle={<ToolbarAddButton onClick={() => setIsOpen(!isOpen)} />}
        dropdownItems={dropdownItems.map(item => (
          <Link
            className="pf-c-dropdown__menu-item"
            key={item.url}
            to={item.url}
          >
            {item.label}
          </Link>
        ))}
      />
    </div>
  );
}

AddDropDownButton.propTypes = {
  dropdownItems: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      url: PropTypes.string.isRequired,
    })
  ).isRequired,
};

export { AddDropDownButton as _AddDropDownButton };
export default AddDropDownButton;
