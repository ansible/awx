import React from 'react';
import {
  useRouteMatch,
  useLocation,
  BrowserRouter,
  Route,
  Switch,
  Redirect,
} from 'react-router-dom';
import { I18n, I18nProvider } from '@lingui/react';

import AppContainer from './components/AppContainer';
import Background from './components/Background';
import NotFound from './screens/NotFound';
import Login from './screens/Login';

import ja from './locales/ja/messages';
import en from './locales/en/messages';
import { isAuthenticated } from './util/auth';
import { getLanguageWithoutRegionCode } from './util/language';

import getRouteConfig from './routeConfig';

const ProtectedRoute = ({ children, ...rest }) =>
  isAuthenticated(document.cookie) ? (
    <Route {...rest}>{children}</Route>
  ) : (
    <Redirect to="/login" />
  );

function App() {
  const catalogs = { en, ja };
  const language = getLanguageWithoutRegionCode(navigator);
  const match = useRouteMatch();
  const { hash, search, pathname } = useLocation();

  return (
    <I18nProvider language={language} catalogs={catalogs}>
      <I18n>
        {({ i18n }) => (
          <Background>
            <Switch>
              <Route exact strict path="/*/">
                <Redirect to={`${pathname.slice(0, -1)}${search}${hash}`} />
              </Route>
              <Route path="/login">
                <Login isAuthenticated={isAuthenticated} />
              </Route>
              <Route exact path="/">
                <Redirect to="/home" />
              </Route>
              <ProtectedRoute>
                <AppContainer navRouteConfig={getRouteConfig(i18n)}>
                  <Switch>
                    {getRouteConfig(i18n)
                      .flatMap(({ routes }) => routes)
                      .map(({ path, screen: Screen }) => (
                        <ProtectedRoute key={path} path={path}>
                          <Screen match={match} />
                        </ProtectedRoute>
                      ))
                      .concat(
                        <ProtectedRoute key="not-found" path="*">
                          <NotFound />
                        </ProtectedRoute>
                      )}
                  </Switch>
                </AppContainer>
              </ProtectedRoute>
            </Switch>
          </Background>
        )}
      </I18n>
    </I18nProvider>
  );
}

export default () => (
  <BrowserRouter basename="/next">
    <App />
  </BrowserRouter>
);
