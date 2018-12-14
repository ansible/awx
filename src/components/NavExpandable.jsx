import React, { Component } from 'react';
import {
  withRouter
} from 'react-router-dom';
import {
  NavExpandable,
  NavItem,
} from '@patternfly/react-core';

class NavExpandableWrapper extends Component {
  constructor (props) {
    super(props);
    // introspect to get any child 'NavItem' components
    const { children } = this.props;
    const navItems = children.filter(({ type }) => type.componentType === NavItem.displayName);

    // Extract a list of 'to' params from the nav items and store it for later. This will create
    // an array of the url paths associated with any child NavItem components.
    this.navItemPaths = navItems.map(item => item.props.to.replace('/#', ''));
  }

  isActiveGroup = () => {
    const { history } = this.props;

    return this.navItemPaths.some(path => history.location.pathname.includes(path));
  };

  render () {
    const { children, staticContext, ...rest } = this.props;
    const isActive = this.isActiveGroup();

    return (
      <NavExpandable
        isActive={isActive}
        isExpanded={isActive}
        {...rest}
      >
        { children }
      </NavExpandable>
    );
  }
}

export default withRouter(NavExpandableWrapper);
