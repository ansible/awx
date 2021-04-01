import React from 'react';
import {
  useRouteMatch,
  useLocation,
  HashRouter,
  Route,
  Switch,
  Redirect,
} from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { i18n } from '@lingui/core';

import { en, es, fr, nl, zh, ja, zu } from 'make-plural/plurals';
import AppContainer from './components/AppContainer';
import Background from './components/Background';
import NotFound from './screens/NotFound';
import Login from './screens/Login';

import japanese from './locales/ja/messages';
import english from './locales/en/messages';
import zulu from './locales/zu/messages';
import french from './locales/fr/messages';
import dutch from './locales/nl/messages';
import chinese from './locales/zh/messages';
import spanish from './locales/es/messages';
import { isAuthenticated } from './util/auth';

import { getLanguageWithoutRegionCode } from './util/language';

import getRouteConfig from './routeConfig';
import SubscriptionEdit from './screens/Setting/Subscription/SubscriptionEdit';

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
          <ProtectedRoute key="not-found" path="*">
            <NotFound />
          </ProtectedRoute>
        )}
    </Switch>
  );
};

const ProtectedRoute = ({ children, ...rest }) =>
  isAuthenticated(document.cookie) ? (
    <Route {...rest}>{children}</Route>
  ) : (
    <Redirect to="/login" />
  );

function App() {
  const catalogs = {
    en: english,
    ja: japanese,
    zu: zulu,
    fr: french,
    es: spanish,
    zh: chinese,
    nl: dutch,
  };
  let language = getLanguageWithoutRegionCode(navigator);
  if (!Object.keys(catalogs).includes(language)) {
    // If there isn't a string catalog available for the browser's
    // preferred language, default to one that has strings.
    language = 'en';
  }
  const { hash, search, pathname } = useLocation();

  i18n.loadLocaleData('en', { plurals: en });
  i18n.loadLocaleData('es', { plurals: es });
  i18n.loadLocaleData('fr', { plurals: fr });
  i18n.loadLocaleData('nl', { plurals: nl });
  i18n.loadLocaleData('zh', { plurals: zh });
  i18n.loadLocaleData('ja', { plurals: ja });
  i18n.loadLocaleData('zu', { plurals: zu });
  i18n.load({
    en: english.messages,
    ja: japanese.messages,
    zu: zulu.messages,
    fr: french.messages,
    nl: dutch.messages,
    zh: chinese.messages,
    es: spanish.messages,
  });
  i18n.activate(language);
  return (
    <I18nProvider i18n={i18n} catalogs={catalogs}>
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
    </I18nProvider>
  );
}

export default () => (
  <HashRouter>
    <App />
  </HashRouter>
);
