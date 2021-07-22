import React, { Component } from 'react';
import PropTypes, { oneOfType, string, arrayOf } from 'prop-types';
import { matchPath, Link, withRouter } from 'react-router-dom';
import { NavExpandable, NavItem } from '@patternfly/react-core';

class NavExpandableGroup extends Component {
  constructor(props) {
    super(props);
    const { routes } = this.props;

    // Extract a list of paths from the route params and store them for later. This creates
    // an array of url paths associated with any NavItem component rendered by this component.
    this.navItemPaths = routes.map(({ path }) => path);
    this.isActiveGroup = this.isActiveGroup.bind(this);
    this.isActivePath = this.isActivePath.bind(this);
  }

  isActiveGroup() {
    return this.navItemPaths.some(this.isActivePath);
  }

  isActivePath(path) {
    const { history } = this.props;
    return Boolean(matchPath(history.location.pathname, { path }));
  }

  render() {
    const { groupId, groupTitle, routes } = this.props;

    if (routes.length === 1 && groupId === 'settings') {
      const [{ path }] = routes;
      return (
        <NavItem itemId={groupId} isActive={this.isActivePath(path)} key={path}>
          <Link to={path}>{groupTitle}</Link>
        </NavItem>
      );
    }

    return (
      <NavExpandable
        isActive={this.isActiveGroup()}
        isExpanded
        groupId={groupId}
        title={groupTitle}
      >
        {routes.map(({ path, title }) => (
          <NavItem
            groupId={groupId}
            isActive={this.isActivePath(path)}
            key={path}
          >
            <Link to={path}>{title}</Link>
          </NavItem>
        ))}
      </NavExpandable>
    );
  }
}

NavExpandableGroup.propTypes = {
  groupId: string.isRequired,
  groupTitle: oneOfType([PropTypes.element, string]).isRequired,
  routes: arrayOf(PropTypes.object).isRequired,
};

export default withRouter(NavExpandableGroup);
