import React from 'react';
import {
  Route,
  Redirect
} from 'react-router-dom';

const ConditionalRedirect = ({ component: Component, shouldRedirect, redirectPath, ...props }) => {
  if (shouldRedirect()) {
    return (
      <Redirect to={{
        pathname: redirectPath,
        state: { from: props.location }
      }}/>
    );
  } else {
    return (
      <Route {...props} render={props => (<Component {...props}/>)} />
    );
  }
};

export default ConditionalRedirect;