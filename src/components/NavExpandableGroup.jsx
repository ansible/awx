import React, { Component } from 'react';
import {
  withRouter
} from 'react-router-dom';
import {
  NavExpandable,
  NavItem,
} from '@patternfly/react-core';

class NavExpandableGroup extends Component {
  constructor (props) {
    super(props);
    const { routes } = this.props;
    // Extract a list of paths from the route params and store them for later. This creates
    // an array of url paths associated with any NavItem component rendered by this component.
    this.navItemPaths = routes.map(({ path }) => path);
  }

  isActiveGroup = () => this.navItemPaths.some(this.isActivePath);

  isActivePath = (path) => {
    const { history } = this.props;

    return history.location.pathname.startsWith(path);
  };

  render () {
    const { routes, groupId, staticContext, ...rest } = this.props;
    const isActive = this.isActiveGroup();

    return (
      <NavExpandable
        isActive={isActive}
        isExpanded={isActive}
        groupId={groupId}
        {...rest}
      >
        {routes.map(({ path, title }) => (
          <NavItem
            groupId={groupId}
            isActive={this.isActivePath(path)}
            key={path}
            to={`/#${path}`}
          >
            {title}
          </NavItem>
        ))}
      </NavExpandable>
    );
  }
}

export default withRouter(NavExpandableGroup);
