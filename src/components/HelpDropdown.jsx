import React, { Component, Fragment } from 'react';
import {
  Dropdown,
  DropdownItem,
  DropdownToggle,
  DropdownPosition,
} from '@patternfly/react-core';
import { QuestionCircleIcon } from '@patternfly/react-icons';
import AboutModal from './About';

class HelpDropdown extends Component {
  state = {
    isOpen: false,
    showAboutModal: false
  };

  render () {
    const { isOpen, showAboutModal } = this.state;
    const dropdownItems = [
      <DropdownItem
        href="https://docs.ansible.com/ansible-tower/latest/html/userguide/index.html"
        target="_blank"
        key="help"
      >
      Help
      </DropdownItem>,
      <DropdownItem
        onClick={() => this.setState({ showAboutModal: true })}
        key="about"
      >
      About
      </DropdownItem>,
    ];

    return (
      <Fragment>
        <Dropdown
          onSelect={() => this.setState({ isOpen: !isOpen })}
          toggle={(
            <DropdownToggle onToggle={(isToggleOpen) => this.setState({ isOpen: isToggleOpen })}>
              <QuestionCircleIcon />
            </DropdownToggle>
          )}
          isOpen={isOpen}
          dropdownItems={dropdownItems}
          position={DropdownPosition.right}
        />
        {showAboutModal
          ? (
            <AboutModal
              isOpen={showAboutModal}
              onAboutModalClose={() => this.setState({ showAboutModal: !showAboutModal })}
            />
          )
          : null }
      </Fragment>
    );
  }
}

export default HelpDropdown;
