import { i18n } from '@lingui/core';
import React, { useState } from 'react';
import {
  Dropdown,
  DropdownItem,
  DropdownToggle,
  DropdownPosition,
  DropdownSeparator,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { SESSION_LANG_KEY } from '../../constants';
import { locales } from '../../i18nLoader';

export default function LanguageFilter() {
  const [isLangOpen, setIsLangOpen] = useState(false);

  const handleLangToggle = (isOpen) => {
    setIsLangOpen(isOpen);
  };

  const handleLangOpen = () => {
    setIsLangOpen(!isLangOpen);
  };

  const handleSelect = (key) => {
    window.localStorage.setItem(SESSION_LANG_KEY, key);
    window.location.reload();
  };

  const handleReset = () => {
    window.localStorage.removeItem(SESSION_LANG_KEY);
    window.location.reload();
  };

  return (
    <Dropdown
      isPlain
      isOpen={isLangOpen}
      position={DropdownPosition.right}
      onSelect={handleLangOpen}
      ouiaId="toolbar-lang-dropdown"
      toggle={
        <DropdownToggle
          onToggle={handleLangToggle}
          aria-label={t`Language`}
          ouiaId="toolbar-lang-dropdown-toggle"
        >
          <span style={{ marginLeft: '10px' }}>{locales[i18n.locale]}</span>
        </DropdownToggle>
      }
      dropdownItems={[
        <DropdownItem isDisabled key="current">
          {window.localStorage.getItem(SESSION_LANG_KEY)
            ? `${locales[i18n.locale]} (${t`current`})`
            : `${locales[i18n.locale]} (${t`browser default`})`}
        </DropdownItem>,
        <DropdownSeparator key="sp1" />,
        ...Object.keys(locales).map((key) => (
          <DropdownItem
            key={key}
            component="button"
            isDisabled={key === i18n.locale}
            onClick={() => handleSelect(key)}
            ouiaId={`lang-dropdown-${key}`}
          >
            {locales[key]}
          </DropdownItem>
        )),
        <DropdownSeparator key="sp2" />,
        <DropdownItem
          key="bdefault"
          component="button"
          onClick={handleReset}
          isDisabled={!window.localStorage.getItem(SESSION_LANG_KEY)}
          ouiaId="reset-to-browser-defaults"
        >
          {t`Reset to browser defaults`}
        </DropdownItem>,
      ]}
    />
  );
}
