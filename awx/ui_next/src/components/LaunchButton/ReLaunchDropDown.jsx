import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Dropdown,
  DropdownToggle,
  DropdownItem,
  DropdownPosition,
  DropdownSeparator,
  DropdownDirection,
} from '@patternfly/react-core';
import { RocketIcon } from '@patternfly/react-icons';

function ReLaunchDropDown({ isPrimary = false, handleRelaunch, i18n }) {
  const [isOpen, setIsOPen] = useState(false);

  const onToggle = () => {
    setIsOPen(prev => !prev);
  };

  const dropdownItems = [
    <DropdownItem
      aria-label={i18n._(t`Relaunch on`)}
      key="relaunch_on"
      component="div"
      isPlainText
    >
      {i18n._(t`Relaunch on`)}
    </DropdownItem>,
    <DropdownSeparator key="separator" />,
    <DropdownItem
      key="relaunch_all"
      aria-label={i18n._(t`Relaunch all hosts`)}
      component="button"
      onClick={() => {
        handleRelaunch({ hosts: 'all' });
      }}
    >
      {i18n._(t`All`)}
    </DropdownItem>,

    <DropdownItem
      key="relaunch_failed"
      aria-label={i18n._(t`Relaunch failed hosts`)}
      component="button"
      onClick={() => {
        handleRelaunch({ hosts: 'failed' });
      }}
    >
      {i18n._(t`Failed hosts`)}
    </DropdownItem>,
  ];

  if (isPrimary) {
    return (
      <Dropdown
        position={DropdownPosition.left}
        direction={DropdownDirection.up}
        isOpen={isOpen}
        dropdownItems={dropdownItems}
        toggle={
          <DropdownToggle
            toggleIndicator={null}
            onToggle={onToggle}
            aria-label={i18n._(`relaunch jobs`)}
            id="relaunch_jobs"
            isPrimary
          >
            {i18n._(t`Relaunch`)}
          </DropdownToggle>
        }
      />
    );
  }

  return (
    <Dropdown
      isPlain
      position={DropdownPosition.right}
      isOpen={isOpen}
      dropdownItems={dropdownItems}
      toggle={
        <DropdownToggle
          toggleIndicator={null}
          onToggle={onToggle}
          aria-label={i18n._(`relaunch jobs`)}
          id="relaunch_jobs"
        >
          <RocketIcon />
        </DropdownToggle>
      }
    />
  );
}

export default withI18n()(ReLaunchDropDown);
