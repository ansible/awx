import React, { useState, useRef, useEffect, Fragment } from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import {
  Dropdown,
  DropdownPosition,
  DropdownItem,
} from '@patternfly/react-core';
import { ToolbarAddButton } from '../PaginatedDataList';
import { toTitleCase } from '../../util/strings';
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
    return (
      <Fragment>
        {dropdownItems.map(item => (
          <DropdownItem key={item.url} component={Link} to={item.url}>
            {toTitleCase(`${i18n._(t`Add`)} ${item.label}`)}
          </DropdownItem>
        ))}
      </Fragment>
    );
  }

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
export default withI18n()(AddDropDownButton);
