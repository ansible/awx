import React, { Fragment } from 'react';
import { ConfigContext } from './context';

import {
  Redirect,
  Switch,
  Route,
} from 'react-router-dom';
import {
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

import api from './api';
import { API_LOGOUT, API_CONFIG } from './endpoints';

import Login from './pages/Login';
import HelpDropdown from './components/HelpDropdown';
import LogoutButton from './components/LogoutButton';
import TowerLogo from './components/TowerLogo';
import NavExpandableGroup from './components/NavExpandableGroup';

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
    const { logo, loginInfo, navLabel, routeGroups = [] } = this.props;

    return (
      api.isAuthenticated () ? (
        <Switch>
          <Route path="/login" render={() => <Redirect to='/home' />} />
          <Route exact path="/" render={() => <Redirect to='/home' />} />
          <Route render={() => (
            <ConfigContext.Provider value={config}>
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
                      <Nav aria-label={navLabel}>
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
                // Extract a flattened array of all route params from the provided route config
                // and use it to render route components.
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
            </ConfigContext.Provider>
          )} />
        </Switch>
      ) : (
        <Switch>
          <Route path="/login" render={() => <Login logo={logo} loginInfo={loginInfo} />} />
          <Redirect to="/login" />
        </Switch>
      )
    );
  }
}

export default App;
