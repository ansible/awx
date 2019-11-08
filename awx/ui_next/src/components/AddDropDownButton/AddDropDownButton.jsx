import React, { useState, useRef, useEffect } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { Dropdown, DropdownPosition } from '@patternfly/react-core';
import { ToolbarAddButton } from '@components/PaginatedDataList';

function AddDropDownButton({ topUrl, bottomUrl, topLabel, bottomLabel }) {
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
        dropdownItems={[
          <Link key="top" className="pf-c-dropdown__menu-item" to={`${topUrl}`}>
            {`${topLabel}`}
          </Link>,
          <Link
            key="bottom"
            className="pf-c-dropdown__menu-item"
            to={`${bottomUrl}`}
          >
            {`${bottomLabel}`}
          </Link>,
        ]}
      />
    </div>
  );
}

export { AddDropDownButton as _AddDropDownButton };
export default withI18n()(withRouter(AddDropDownButton));
