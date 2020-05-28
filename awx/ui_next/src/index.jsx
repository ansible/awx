import React from 'react';
import ReactDOM from 'react-dom';
import { Route, Switch, Redirect } from 'react-router-dom';
import { I18n } from '@lingui/react';

import '@patternfly/react-core/dist/styles/base.css';

import { isAuthenticated } from './util/auth';
import Background from './components/Background';
import NotFound from './screens/NotFound';
import Login from './screens/Login';

import App from './App';
import RootProvider from './RootProvider';
import { BrandName } from './variables';
import getRouteConfig from './routeConfig';

// eslint-disable-next-line import/prefer-default-export
export function main(render) {
  const el = document.getElementById('app');
  document.title = `Ansible ${BrandName}`;

  const removeTrailingSlash = (
    <Route
      exact
      strict
      path="/*/"
      render={({
        history: {
          location: { pathname, search, hash },
        },
      }) => <Redirect to={`${pathname.slice(0, -1)}${search}${hash}`} />}
    />
  );

  const AppRoute = ({ auth, children, ...rest }) =>
    // eslint-disable-next-line no-nested-ternary
    auth ? (
      isAuthenticated(document.cookie) ? (
        <Route {...rest}>{children}</Route>
      ) : (
        <Redirect to="/login" />
      )
    ) : isAuthenticated(document.cookie) ? (
      <Redirect to="/home" />
    ) : (
      <Route {...rest}>{children}</Route>
    );

  return render(
    <RootProvider>
      <I18n>
        {({ i18n }) => (
          <Background>
            <Switch>
              {removeTrailingSlash}
              <AppRoute path="/login">
                <Login isAuthenticated={isAuthenticated} />
              </AppRoute>
              <AppRoute exact path="/">
                <Login isAuthenticated={isAuthenticated} />
              </AppRoute>
              <AppRoute auth>
                <App routeConfig={getRouteConfig(i18n)}>
                  <Switch>
                    {getRouteConfig(i18n)
                      .flatMap(({ routes }) => routes)
                      .map(({ path, screen: Screen }) => (
                        <AppRoute
                          auth
                          key={path}
                          path={path}
                          render={({ match }) => <Screen match={match} />}
                        />
                      ))
                      .concat(
                        <AppRoute auth key="not-found" path="*">
                          <NotFound />
                        </AppRoute>
                      )}
                  </Switch>
                </App>
              </AppRoute>
            </Switch>
          </Background>
        )}
      </I18n>
    </RootProvider>,
    el || document.createElement('div')
  );
}

main(ReactDOM.render);
