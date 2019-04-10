import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';
import { I18n } from '@lingui/react';
import {
  Dropdown,
  DropdownItem,
  DropdownToggle,
  DropdownPosition,
  Toolbar,
  ToolbarGroup,
  ToolbarItem,
  Tooltip
} from '@patternfly/react-core';
import {
  QuestionCircleIcon,
  UserIcon,
} from '@patternfly/react-icons';

const DOCLINK = 'https://docs.ansible.com/ansible-tower/latest/html/userguide/index.html';

class PageHeaderToolbar extends Component {
  constructor (props) {
    super(props);
    this.state = {
      isHelpOpen: false,
      isUserOpen: false,
    };

    this.onHelpSelect = this.onHelpSelect.bind(this);
    this.onHelpToggle = this.onHelpToggle.bind(this);
    this.onUserSelect = this.onUserSelect.bind(this);
    this.onUserToggle = this.onUserToggle.bind(this);
  }

  onHelpSelect () {
    const { isHelpOpen } = this.state;

    this.setState({ isHelpOpen: !isHelpOpen });
  }

  onUserSelect () {
    const { isUserOpen } = this.state;

    this.setState({ isUserOpen: !isUserOpen });
  }

  onHelpToggle (isOpen) {
    this.setState({ isHelpOpen: isOpen });
  }

  onUserToggle (isOpen) {
    this.setState({ isUserOpen: isOpen });
  }

  render () {
    const { isHelpOpen, isUserOpen } = this.state;
    const { isAboutDisabled, onAboutClick, onLogoutClick } = this.props;

    return (
      <I18n>
        {({ i18n }) => (
          <Toolbar>
            <ToolbarGroup>
              <Tooltip
                position="left"
                content={
                  <div>Help</div>
                }
              >
                <ToolbarItem>
                  <Dropdown
                    isPlain
                    isOpen={isHelpOpen}
                    position={DropdownPosition.right}
                    onSelect={this.onHelpSelect}
                    toggle={(
                      <DropdownToggle
                        onToggle={this.onHelpToggle}
                      >
                        <QuestionCircleIcon />
                      </DropdownToggle>
                    )}
                    dropdownItems={[
                      <DropdownItem
                        key="help"
                        target="_blank"
                        href={DOCLINK}
                      >
                        {i18n._(t`Help`)}
                      </DropdownItem>,
                      <DropdownItem
                        key="about"
                        component="button"
                        isDisabled={isAboutDisabled}
                        onClick={onAboutClick}
                      >
                        {i18n._(t`About`)}
                      </DropdownItem>
                    ]}
                  />
                </ToolbarItem>
              </Tooltip>
              <Tooltip
                position="left"
                content={
                  <div>User</div>
                }
              >
                <ToolbarItem>
                  <Dropdown
                    isPlain
                    isOpen={isUserOpen}
                    position={DropdownPosition.right}
                    onSelect={this.onUserSelect}
                    toggle={(
                      <DropdownToggle
                        onToggle={this.onUserToggle}
                      >
                        <UserIcon />
                        &nbsp; User Name
                      </DropdownToggle>
                    )}
                    dropdownItems={[
                      <DropdownItem
                        key="user"
                        href="#/home"
                      >
                        {i18n._(t`User Details`)}
                      </DropdownItem>,
                      <DropdownItem
                        key="logout"
                        component="button"
                        onClick={onLogoutClick}
                      >
                        {i18n._(t`Logout`)}
                      </DropdownItem>
                    ]}
                  />
                </ToolbarItem>
              </Tooltip>
            </ToolbarGroup>
          </Toolbar>
        )}
      </I18n>
    );
  }
}

PageHeaderToolbar.propTypes = {
  isAboutDisabled: PropTypes.bool,
  onAboutClick: PropTypes.func.isRequired,
  onLogoutClick: PropTypes.func.isRequired,
};

PageHeaderToolbar.defaultProps = {
  isAboutDisabled: false,
};

export default PageHeaderToolbar;
