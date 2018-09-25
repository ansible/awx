import React from 'react';
import { render } from 'react-dom';
import {
  HashRouter as Router,
  Route,
  Link,
  Redirect
} from 'react-router-dom';

import api from './api';

import About from './components/About';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import Organizations from './components/Organizations';

const AuthenticatedRoute = ({ component: Component, ...rest }) => (
  <Route {...rest} render={props => (
    api.isAuthenticated() ? (
      <Component {...props}/>
    ) : (
      <Redirect to={{
        pathname: '/login',
        state: { from: props.location }
      }}/>
    )
  )}/>
)

const App = () => (
  <Router>
    <div>
      <Route path="/login" component={Login} />
      <AuthenticatedRoute exact path="/" component={Dashboard} />
      <AuthenticatedRoute exact path="/about" component={About} />
      <AuthenticatedRoute exact path="/organizations" component={Organizations} />
    </div>
  </Router>
);

const el = document.getElementById('app');

render(<App />, el);
