import React, { Fragment } from 'react';
import { ConfigContext } from './context';

import {
  HashRouter as Router,
  Redirect,
  Switch,
  withRouter,
  Route,
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

    // initialize with a closed navbar if window size is small
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
    const { config, isNavOpen } = this.state;
    // extract a flattened array of all routes from the provided route config
    const { logo, loginInfo, routeGroups = [] } = this.props;

    return (
      <Router>
        <I18nProvider
          language={languageWithoutRegionCode}
          catalogs={catalogs}
        >
          <I18n>
            {({ i18n }) => (
              api.isAuthenticated () ? (
                <ConfigContext.Provider value={config}>
                  <Switch>
                    <Route path="/login" render={() => <Redirect to='/home' />} />
                    <Route exact path="/" render={() => <Redirect to='/home' />} />
                    <Route render={() => (
                      <Fragment>
                        <BackgroundImage src={backgroundConfig} />
                        <Page
                          usecondensed="True"
                          header={(
                            <PageHeader
                              showNavToggle
                              onNavToggle={() => this.onNavToggle()}
                              logo={(
                                <TowerLogo
                                  onClick={this.onLogoClick}
                                />
                              )}
                              toolbar={(
                                <Toolbar>
                                  <ToolbarGroup>
                                    <ToolbarItem>
                                      <HelpDropdown />
                                    </ToolbarItem>
                                    <ToolbarItem>
                                      <LogoutButton
                                        onDevLogout={() => this.onDevLogout()}
                                      />
                                    </ToolbarItem>
                                  </ToolbarGroup>
                                </Toolbar>
                              )}
                            />
                          )}
                          sidebar={(
                            <PageSidebar
                              isNavOpen={isNavOpen}
                              nav={(
                                <Nav aria-label={i18n._("Primary Navigation")}>
                                  <NavList>
                                  {
                                    routeGroups.map(params => <NavExpandableGroup key={params.groupId} {...params} />)
                                  }
                                  </NavList>
                                </Nav>
                              )}
                            />
                          )}
                        >
                        {
                          //
                          // Extract a flattened array of all route params from the provided route groups
                          // and use it to create the route components.
                          //
                          // [{ routes }, { routes }] -> [route, route, route] -> (<Route/><Route/><Route/>)
                          //
                          routeGroups
                            .reduce((allRoutes, { routes }) => allRoutes.concat(routes), [])
                            .map(({ component: Component, path }) => (
                              <Route key={path} path={path} render={params => <Component {...params } />} />
                            ))
                        }
                        </Page>
                      </Fragment>
                    )} />
                  </Switch>
                </ConfigContext.Provider>
              ) : (
                <Switch>
                  <Route path="/login" render={() => <Login logo={logo} loginInfo={loginInfo} />} />
                  <Redirect to="/login" />
                </Switch>
              )
            )}
          </I18n>
        </I18nProvider>
      </Router>
    );
  }
}

export default App;
