import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Dropdown,
  DropdownItem,
  DropdownToggle,
  DropdownPosition,
  PageHeaderTools,
  PageHeaderToolsGroup,
  PageHeaderToolsItem,
  Tooltip,
} from '@patternfly/react-core';
import { QuestionCircleIcon, UserIcon } from '@patternfly/react-icons';

const DOCLINK =
  'https://docs.ansible.com/ansible-tower/latest/html/userguide/index.html';

function PageHeaderToolbar({
  isAboutDisabled,
  onAboutClick,
  onLogoutClick,
  loggedInUser,
  i18n,
}) {
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [isUserOpen, setIsUserOpen] = useState(false);

  const handleHelpSelect = () => {
    setIsHelpOpen(!isHelpOpen);
  };

  const handleUserSelect = () => {
    setIsUserOpen(!isUserOpen);
  };

  return (
    <PageHeaderTools>
      <PageHeaderToolsGroup>
        <Tooltip position="left" content={<div>{i18n._(t`Info`)}</div>}>
          <PageHeaderToolsItem>
            <Dropdown
              isPlain
              isOpen={isHelpOpen}
              position={DropdownPosition.right}
              onSelect={handleHelpSelect}
              toggle={
                <DropdownToggle
                  onToggle={setIsHelpOpen}
                  aria-label={i18n._(t`Info`)}
                >
                  <QuestionCircleIcon />
                </DropdownToggle>
              }
              dropdownItems={[
                <DropdownItem key="help" target="_blank" href={DOCLINK}>
                  {i18n._(t`Help`)}
                </DropdownItem>,
                <DropdownItem
                  key="about"
                  component="button"
                  isDisabled={isAboutDisabled}
                  onClick={onAboutClick}
                >
                  {i18n._(t`About`)}
                </DropdownItem>,
              ]}
            />
          </PageHeaderToolsItem>
        </Tooltip>
        <Tooltip position="left" content={<div>{i18n._(t`User`)}</div>}>
          <PageHeaderToolsItem>
            <Dropdown
              id="toolbar-user-dropdown"
              isPlain
              isOpen={isUserOpen}
              position={DropdownPosition.right}
              onSelect={handleUserSelect}
              toggle={
                <DropdownToggle onToggle={setIsUserOpen}>
                  <UserIcon />
                  {loggedInUser && (
                    <span style={{ marginLeft: '10px' }}>
                      {loggedInUser.username}
                    </span>
                  )}
                </DropdownToggle>
              }
              dropdownItems={[
                <DropdownItem
                  key="user"
                  href={
                    loggedInUser ? `/users/${loggedInUser.id}/details` : '/home'
                  }
                >
                  {i18n._(t`User Details`)}
                </DropdownItem>,
                <DropdownItem
                  key="logout"
                  component="button"
                  onClick={onLogoutClick}
                  id="logout-button"
                >
                  {i18n._(t`Logout`)}
                </DropdownItem>,
              ]}
            />
          </PageHeaderToolsItem>
        </Tooltip>
      </PageHeaderToolsGroup>
    </PageHeaderTools>
  );
}

PageHeaderToolbar.propTypes = {
  isAboutDisabled: PropTypes.bool,
  onAboutClick: PropTypes.func.isRequired,
  onLogoutClick: PropTypes.func.isRequired,
};

PageHeaderToolbar.defaultProps = {
  isAboutDisabled: false,
};

export default withI18n()(PageHeaderToolbar);
