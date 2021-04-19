import React, { useState } from 'react';

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

function ReLaunchDropDown({ isPrimary = false, handleRelaunch, ouiaId }) {
  const [isOpen, setIsOPen] = useState(false);

  const onToggle = () => {
    setIsOPen(prev => !prev);
  };

  const dropdownItems = [
    <DropdownItem
      aria-label={t`Relaunch on`}
      key="relaunch_on"
      component="div"
      isPlainText
    >
      {t`Relaunch on`}
    </DropdownItem>,
    <DropdownSeparator key="separator" />,
    <DropdownItem
      key="relaunch_all"
      aria-label={t`Relaunch all hosts`}
      component="button"
      onClick={() => {
        handleRelaunch({ hosts: 'all' });
      }}
    >
      {t`All`}
    </DropdownItem>,

    <DropdownItem
      key="relaunch_failed"
      aria-label={t`Relaunch failed hosts`}
      component="button"
      onClick={() => {
        handleRelaunch({ hosts: 'failed' });
      }}
    >
      {t`Failed hosts`}
    </DropdownItem>,
  ];

  if (isPrimary) {
    return (
      <Dropdown
        ouiaId={ouiaId}
        position={DropdownPosition.left}
        direction={DropdownDirection.up}
        isOpen={isOpen}
        dropdownItems={dropdownItems}
        toggle={
          <DropdownToggle
            toggleIndicator={null}
            onToggle={onToggle}
            aria-label={t`relaunch jobs`}
            id="relaunch_jobs"
            isPrimary
          >
            {t`Relaunch`}
          </DropdownToggle>
        }
      />
    );
  }

  return (
    <Dropdown
      ouiaId={ouiaId}
      isPlain
      position={DropdownPosition.right}
      isOpen={isOpen}
      dropdownItems={dropdownItems}
      toggle={
        <DropdownToggle
          toggleIndicator={null}
          onToggle={onToggle}
          aria-label={t`relaunch jobs`}
          id="relaunch_jobs"
        >
          <RocketIcon />
        </DropdownToggle>
      }
    />
  );
}

export default ReLaunchDropDown;
