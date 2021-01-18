import React, { useState } from 'react';
import {
  useRouteMatch,
  useLocation,
  HashRouter,
  Route,
  Switch,
  Redirect,
} from 'react-router-dom';
import { I18n, I18nProvider } from '@lingui/react';

import AppContainer from './components/AppContainer';
import Background from './components/Background';
import NotFound from './screens/NotFound';
import Login from './screens/Login';
import { MeAPI, UsersAPI, OrganizationsAPI } from './api';

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
  const [userData, setUserData] = useState({});
  const [isOrgAdmin, setIsOrgAdmin] = useState(false);
  const [isNotifAdmin, setIsNotifAdmin] = useState(false);
  const [fetchUserError, setFetchUserError] = useState(null);
  const [isUserDataReady, setIsUserDataReady] = useState(false);

  let language = getLanguageWithoutRegionCode(navigator);
  if (!Object.keys(catalogs).includes(language)) {
    // If there isn't a string catalog available for the browser's
    // preferred language, default to one that has strings.
    language = 'en';
  }
  const match = useRouteMatch();
  const { hash, search, pathname } = useLocation();

  const fetchUserData = async () => {
    try {
      const [
        {
          data: {
            results: [me],
          },
        },
      ] = await Promise.all([MeAPI.read()]);

      const [
        {
          data: { count: adminOrgCount },
        },
        {
          data: { count: notifAdminCount },
        },
      ] = await Promise.all([
        UsersAPI.readAdminOfOrganizations(me?.id),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
      ]);
      setUserData(me);
      setIsOrgAdmin(Boolean(adminOrgCount));
      setIsNotifAdmin(Boolean(notifAdminCount));
      setIsUserDataReady(true);
    } catch (err) {
      setFetchUserError(err);
    }
  };

  const user = {
    isSuperUser: Boolean(userData?.is_superuser),
    isSystemAuditor: Boolean(userData?.is_system_auditor),
    isOrgAdmin,
    isNotifAdmin,
  };

  const handleSetUserIsDataReady = () => setIsUserDataReady(false);

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
                <Login
                  isAuthenticated={isAuthenticated}
                  fetchUserData={fetchUserData}
                  userError={fetchUserError}
                  isUserDataReady={isUserDataReady}
                />
              </Route>
              <Route exact path="/">
                <Redirect to="/home" />
              </Route>
              <ProtectedRoute>
                <AppContainer
                  handleSetIsReady={handleSetUserIsDataReady}
                  navRouteConfig={getRouteConfig(i18n, user)}
                >
                  <Switch>
                    {getRouteConfig(i18n, user)
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
  <HashRouter>
    <App />
  </HashRouter>
);
