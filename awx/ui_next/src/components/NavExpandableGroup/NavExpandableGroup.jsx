import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
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

    return history.location.pathname.startsWith(path);
  }

  render() {
    const { groupId, groupTitle, routes } = this.props;
    const isActive = this.isActiveGroup();

    return (
      <NavExpandable
        isActive={isActive}
        isExpanded={isActive}
        groupId={groupId}
        title={groupTitle}
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

NavExpandableGroup.propTypes = {
  groupId: PropTypes.string.isRequired,
  groupTitle: PropTypes.string.isRequired,
  routes: PropTypes.arrayOf(PropTypes.object).isRequired,
};

export default withRouter(NavExpandableGroup);
