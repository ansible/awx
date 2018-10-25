import React from 'react';
import {
  Route,
  Redirect
} from 'react-router-dom';

const ConditionalRedirect = ({
  component: Component,
  shouldRedirect,
  redirectPath,
  location,
  ...props
}) => (shouldRedirect() ? (
  <Redirect to={{
    pathname: redirectPath,
    state: { from: location }
  }}
  />
) : (
  <Route {...props} render={rest => (<Component {...rest} />)} />
));

export default ConditionalRedirect;
