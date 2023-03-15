import React, { useEffect } from 'react';
import {
  useRouteMatch,
  useLocation,
  HashRouter,
  Route,
  Switch,
  Redirect,
  useHistory,
} from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';
import { I18nProvider } from '@lingui/react';
import { i18n } from '@lingui/core';
import { Card, PageSection } from '@patternfly/react-core';
import {
  ConfigProvider,
  useAuthorizedPath,
  useUserProfile,
} from 'contexts/Config';
import { SessionProvider, useSession } from 'contexts/Session';
import AppContainer from 'components/AppContainer';
import Background from 'components/Background';
import ContentError from 'components/ContentError';
import NotFound from 'screens/NotFound';
import Login from 'screens/Login';
import { isAuthenticated } from 'util/auth';
import { getLanguageWithoutRegionCode } from 'util/language';
import Metrics from 'screens/Metrics';
import SubscriptionEdit from 'screens/Setting/Subscription/SubscriptionEdit';
import useTitle from 'hooks/useTitle';
import { dynamicActivate } from './i18nLoader';
import getRouteConfig from './routeConfig';
import { SESSION_REDIRECT_URL } from './constants';

function ErrorFallback({ error }) {
  return (
    <PageSection>
      <Card>
        <ContentError error={error} />
      </Card>
    </PageSection>
  );
}

const RenderAppContainer = () => {
  const userProfile = useUserProfile();
  const navRouteConfig = getRouteConfig(userProfile);

  return (
    <AppContainer navRouteConfig={navRouteConfig}>
      <AuthorizedRoutes routeConfig={navRouteConfig} />
    </AppContainer>
  );
};

const AuthorizedRoutes = ({ routeConfig }) => {
  const isAuthorized = useAuthorizedPath();
  const match = useRouteMatch();

  if (!isAuthorized) {
    return (
      <Switch>
        <ProtectedRoute
          key="/subscription_management"
          path="/subscription_management"
        >
          <PageSection>
            <Card>
              <SubscriptionEdit />
            </Card>
          </PageSection>
        </ProtectedRoute>
        <Route path="*">
          <Redirect to="/subscription_management" />
        </Route>
      </Switch>
    );
  }

  return (
    <Switch>
      {routeConfig
        .flatMap(({ routes }) => routes)
        .map(({ path, screen: Screen }) => (
          <ProtectedRoute key={path} path={path}>
            <Screen match={match} />
          </ProtectedRoute>
        ))
        .concat(
          <ProtectedRoute key="metrics" path="/metrics">
            <Metrics />
          </ProtectedRoute>,
          <ProtectedRoute key="not-found" path="*">
            <NotFound />
          </ProtectedRoute>
        )}
    </Switch>
  );
};

export function ProtectedRoute({ children, ...rest }) {
  const {
    authRedirectTo,
    isUserBeingLoggedOut,
    loginRedirectOverride,
    setAuthRedirectTo,
  } = useSession();
  const location = useLocation();

  useEffect(() => {
    setAuthRedirectTo(
      authRedirectTo === '/logout'
        ? '/'
        : `${location.pathname}${location.search}`
    );
  });

  if (isAuthenticated(document.cookie)) {
    return (
      <Route {...rest}>
        <ErrorBoundary FallbackComponent={ErrorFallback}>
          {children}
        </ErrorBoundary>
      </Route>
    );
  }

  if (
    loginRedirectOverride &&
    !window.location.href.includes('/login') &&
    !isUserBeingLoggedOut
  ) {
    window.location.replace(loginRedirectOverride);
    return null;
  }
  return <Redirect to="/login" />;
}

function App() {
  const history = useHistory();
  const { hash, search, pathname } = useLocation();
  const searchParams = Object.fromEntries(new URLSearchParams(search));
  const pseudolocalization =
    searchParams.pseudolocalization === 'true' || false;
  const language =
    searchParams.lang || getLanguageWithoutRegionCode(navigator) || 'en';

  useEffect(() => {
    dynamicActivate(language, pseudolocalization);
  }, [language, pseudolocalization]);

  useTitle();

  const redirectURL = window.sessionStorage.getItem(SESSION_REDIRECT_URL);
  if (redirectURL) {
    window.sessionStorage.removeItem(SESSION_REDIRECT_URL);
    if (redirectURL !== '/' || redirectURL !== '/home')
      history.replace(redirectURL);
  }

  return (
    <I18nProvider i18n={i18n}>
      <Background>
        <SessionProvider>
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
              <ConfigProvider>
                <RenderAppContainer />
              </ConfigProvider>
            </ProtectedRoute>
          </Switch>
        </SessionProvider>
      </Background>
    </I18nProvider>
  );
}

export default () => (
  <HashRouter>
    <App />
  </HashRouter>
);
