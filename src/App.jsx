import React, { Component, Fragment } from 'react';
import { global_breakpoint_md } from '@patternfly/react-tokens';
import {
  Nav,
  NavList,
  Page,
  PageHeader,
  PageSidebar,
} from '@patternfly/react-core';

import About from './components/About';
import NavExpandableGroup from './components/NavExpandableGroup';
import TowerLogo from './components/TowerLogo';
import PageHeaderToolbar from './components/PageHeaderToolbar';
import { ConfigContext } from './context';

class App extends Component {
  constructor (props) {
    super(props);

    // initialize with a closed navbar if window size is small
    const isNavOpen = typeof window !== 'undefined'
      && window.innerWidth >= parseInt(global_breakpoint_md.value, 10);

    this.state = {
      ansible_version: null,
      version: null,
      isAboutModalOpen: false,
      isNavOpen,
    };

    this.fetchConfig = this.fetchConfig.bind(this);
    this.onLogout = this.onLogout.bind(this);
    this.onAboutModalClose = this.onAboutModalClose.bind(this);
    this.onAboutModalOpen = this.onAboutModalOpen.bind(this);
    this.onLogoClick = this.onLogoClick.bind(this);
    this.onNavToggle = this.onNavToggle.bind(this);
  };

  componentDidMount () {
    this.fetchConfig();
  }

  async onLogout () {
    const { api } = this.props;

    await api.logout();
    window.location.replace('/#/login')
  }

  async fetchConfig () {
    const { api } = this.props;

    try {
      const { data: { ansible_version, version } } = await api.getConfig();
      this.setState({ ansible_version, version });
    } catch (err) {
      this.setState({ ansible_version: null, version: null });
    }
  }

  onAboutModalOpen () {
    this.setState({ isAboutModalOpen: true });
  }

  onAboutModalClose () {
    this.setState({ isAboutModalOpen: false });
  }

  onNavToggle () {
    this.setState(({ isNavOpen }) => ({ isNavOpen: !isNavOpen }));
  }

  onLogoClick () {
    this.setState({ activeGroup: 'views_group' });
  }

  render () {
    const {
      ansible_version,
      isAboutModalOpen,
      isNavOpen,
      version,
    } = this.state;
    const {
      render,
      routeGroups = [],
      navLabel = '',
    } = this.props;

    const config = {
      ansible_version,
      version,
    };

    return (
      <Fragment>
        <Page
          usecondensed="True"
          header={(
            <PageHeader
              showNavToggle
              onNavToggle={this.onNavToggle}
              logo={
                <TowerLogo
                  onClick={this.onLogoClick}
                />
              }
              toolbar={
                <PageHeaderToolbar
                  isAboutDisabled={!version}
                  onAboutClick={this.onAboutModalOpen}
                  onLogoutClick={this.onLogout}
                />
              }
            />
          )}
          sidebar={
            <PageSidebar
              isNavOpen={isNavOpen}
              nav={(
                <Nav aria-label={navLabel}>
                  <NavList>
                    {routeGroups.map(params => (
                      <NavExpandableGroup
                        key={params.groupId}
                        {...params}
                      />
                    ))}
                  </NavList>
                </Nav>
              )}
            />
          }
        >
          <ConfigContext.Provider value={config}>
            { render ? render({ routeGroups }) : '' }
          </ConfigContext.Provider>
        </Page>
        <About
          ansible_version={ansible_version}
          version={version}
          isOpen={isAboutModalOpen}
          onClose={this.onAboutModalClose}
        />
      </Fragment>
    );
  }
}

export default App;
