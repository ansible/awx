import React from 'react';
import PropTypes, { oneOfType, string, arrayOf } from 'prop-types';
import { matchPath, Link, useHistory } from 'react-router-dom';
import { NavExpandable, NavItem } from '@patternfly/react-core';

function NavExpandableGroup(props) {
  const history = useHistory();
  const { groupId, groupTitle, routes } = props;

  // Extract a list of paths from the route params and store them for later. This creates
  // an array of url paths associated with any NavItem component rendered by this component.
  const navItemPaths = routes.map(({ path }) => path);

  const isActive = navItemPaths.some(isActivePath);

  function isActivePath(path) {
    return Boolean(matchPath(history.location.pathname, { path }));
  }

  if (routes.length === 1 && groupId === 'settings') {
    const [{ path }] = routes;
    return (
      <NavItem
        itemId={groupId}
        isActive={isActivePath(path)}
        key={path}
        // ouiaId={path}
      >
        <Link to={path}>{groupTitle}</Link>
      </NavItem>
    );
  }

  return (
    <NavExpandable
      isActive={isActive}
      isExpanded
      groupId={groupId}
      ouiaId={groupId}
      title={groupTitle}
    >
      {routes.map(({ path, title }) => (
        <NavItem
          groupId={groupId}
          isActive={isActivePath(path)}
          key={path}
          // ouiaId={path}
        >
          <Link to={path}>{title}</Link>
        </NavItem>
      ))}
    </NavExpandable>
  );
}

NavExpandableGroup.propTypes = {
  groupId: string.isRequired,
  groupTitle: oneOfType([PropTypes.element, string]).isRequired,
  routes: arrayOf(PropTypes.object).isRequired,
};

export default NavExpandableGroup;
