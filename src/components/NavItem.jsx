import React from 'react';
import { withRouter } from 'react-router-dom';
import { NavItem } from '@patternfly/react-core';

export default withRouter(({ history, to, staticContext, ...props }) => (
  <NavItem to={to} isActive={history.location.pathname.includes(to.replace('/#', ''))} {...props} />
));
