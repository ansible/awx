import React, { Fragment } from 'react';
import { ConfigContext } from './context';

import {
  HashRouter as Router,
  Redirect,
  Switch,
  withRouter
} from 'react-router-dom';
import {
  BackgroundImage,
  BackgroundImageSrc,
  Nav,
  NavList,
  Page,
  PageHeader,
  PageSidebar,
  Toolbar,
  ToolbarGroup,
  ToolbarItem
} from '@patternfly/react-core';
import { global_breakpoint_md as breakpointMd } from '@patternfly/react-tokens';
import { I18nProvider, I18n } from '@lingui/react';
import { t } from '@lingui/macro';

import api from './api';
import { API_LOGOUT, API_CONFIG } from './endpoints';

import ja from '../build/locales/ja/messages';
import en from '../build/locales/en/messages';

import Login from './pages/Login';
import HelpDropdown from './components/HelpDropdown';
import LogoutButton from './components/LogoutButton';
import TowerLogo from './components/TowerLogo';
import ConditionalRedirect from './components/ConditionalRedirect';
import NavExpandableGroup from './components/NavExpandableGroup';

const catalogs = { en, ja };
// Derive the language and the region from global user agent data. Example: es-US
// https://developer.mozilla.org/en-US/docs/Web/API/Navigator
const language = (navigator.languages && navigator.languages[0])
  || navigator.language
  || navigator.userLanguage;
const languageWithoutRegionCode = language.toLowerCase().split(/[_-]+/)[0];

// define background src image config
const backgroundConfig = {
  [BackgroundImageSrc.lg]: '/assets/images/pfbg_1200.jpg',
  [BackgroundImageSrc.md]: '/assets/images/pfbg_992.jpg',
  [BackgroundImageSrc.md2x]: '/assets/images/pfbg_992@2x.jpg',
  [BackgroundImageSrc.sm]: '/assets/images/pfbg_768.jpg',
  [BackgroundImageSrc.sm2x]: '/assets/images/pfbg_768@2x.jpg',
  [BackgroundImageSrc.xl]: '/assets/images/pfbg_2000.jpg',
  [BackgroundImageSrc.xs]: '/assets/images/pfbg_576.jpg',
  [BackgroundImageSrc.xs2x]: '/assets/images/pfbg_576@2x.jpg',
  [BackgroundImageSrc.filter]: '/assets/images/background-filter.svg'
};

class App extends React.Component {
  constructor(props) {
    super(props);

    const isNavOpen = typeof window !== 'undefined'
      && window.innerWidth >= parseInt(breakpointMd.value, 10);

    this.state = {
      isNavOpen,
      config: {},
      error: false,
    };
  };

  onNavToggle = () => {
    this.setState(({ isNavOpen }) => ({ isNavOpen: !isNavOpen }));
  };

  onLogoClick = () => {
    this.setState({ activeGroup: 'views_group' });
  }

  onDevLogout = async () => {
    await api.get(API_LOGOUT);
    this.setState({ activeGroup: 'views_group', activeItem: 'views_group_dashboard' });
  }

  async componentDidMount() {
    // Grab our config data from the API and store in state
    try {
      const { data } = await api.get(API_CONFIG);
      this.setState({ config: data });
    } catch (error) {
      this.setState({ error });
    }
  }

  render () {
    const { isNavOpen } = this.state;
    const { logo, loginInfo, history, routeConfig = [] } = this.props;
    // extract a flattened array of all routes from the provided route config
    const allRoutes = routeConfig.reduce((flattened, { routes }) => flattened.concat(routes), []);

    return (
      <Router>
        <I18nProvider
          language={languageWithoutRegionCode}
          catalogs={catalogs}
        >
          <I18n>
            {({ i18n }) => (
              <Fragment>
                <ConfigContext.Provider>
                  <BackgroundImage src={backgroundConfig} />
                  <Switch>
                    <ConditionalRedirect
                      shouldRedirect={() => api.isAuthenticated()}
                      redirectPath="/"
                      path="/login"
                      component={() => <Login logo={logo} loginInfo={loginInfo} />}
                    />
                    <Fragment>
                      <Page
                        usecondensed="True"
                        header={(
                          <PageHeader
                            logo={<TowerLogo onClick={this.onLogoClick} />}
                            toolbar={(
                              <Toolbar>
                                <ToolbarGroup>
                                  <ToolbarItem>
                                    <HelpDropdown />
                                  </ToolbarItem>
                                  <ToolbarItem>
                                    <LogoutButton onDevLogout={() => this.onDevLogout()} />
                                  </ToolbarItem>
                                </ToolbarGroup>
                              </Toolbar>
                            )}
                            showNavToggle
                            onNavToggle={this.onNavToggle}
                          />
                        )}
                        sidebar={(
                          <PageSidebar
                            isNavOpen={isNavOpen}
                            nav={(
                              <Nav aria-label={i18n._("Primary Navigation")}>
                                <NavList>
                                  { routeConfig.map(({ groupId, routes, title }) => (
                                    <NavExpandableGroup
                                      key={groupId}
                                      groupId={groupId}
                                      title={i18n._(title)}
                                      routes={routes.map(route => ({
                                        path: route.path,
                                        component: route.component,
                                        title: i18n._(route.title)
                                      }))}
                                    />
                                  ))}
                                </NavList>
                              </Nav>
                            )}
                          />
                        )}
                      >
                        <ConditionalRedirect
                          shouldRedirect={() => !api.isAuthenticated()}
                          redirectPath="/login"
                          exact path="/"
                          component={() => (<Redirect to="/home" />)}
                        />
                        { allRoutes.map(({ component, path }) => (
                          <ConditionalRedirect
                            key={path}
                            path={path}
                            redirectPath="/login"
                            shouldRedirect={() => !api.isAuthenticated()}
                            component={component}
                          />
                        ))}
                      </Page>
                    </Fragment>
                  </Switch>
                </ConfigContext.Provider>
              </Fragment>
            )}
          </I18n>
        </I18nProvider>
      </Router>
    );
  }
}

export default App;
