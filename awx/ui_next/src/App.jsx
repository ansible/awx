import React, { Component, Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { global_breakpoint_md } from '@patternfly/react-tokens';
import {
  Nav,
  NavList,
  Page,
  PageHeader as PFPageHeader,
  PageSidebar,
} from '@patternfly/react-core';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import { ConfigAPI, MeAPI, RootAPI } from '@api';
import About from '@components/About';
import AlertModal from '@components/AlertModal';
import NavExpandableGroup from '@components/NavExpandableGroup';
import BrandLogo from '@components/BrandLogo';
import PageHeaderToolbar from '@components/PageHeaderToolbar';
import ErrorDetail from '@components/ErrorDetail';
import { ConfigProvider } from '@contexts/Config';

const PageHeader = styled(PFPageHeader)`
  & .pf-c-page__header-brand-link {
    color: inherit;

    &:hover {
      color: inherit;
    }

    & svg {
      height: 76px;
    }
  }
`;

class App extends Component {
  constructor(props) {
    super(props);

    // initialize with a closed navbar if window size is small
    const isNavOpen =
      typeof window !== 'undefined' &&
      window.innerWidth >= parseInt(global_breakpoint_md.value, 10);

    this.state = {
      ansible_version: null,
      custom_virtualenvs: null,
      me: null,
      version: null,
      isAboutModalOpen: false,
      isNavOpen,
      configError: null,
    };

    this.handleLogout = this.handleLogout.bind(this);
    this.handleAboutClose = this.handleAboutClose.bind(this);
    this.handleAboutOpen = this.handleAboutOpen.bind(this);
    this.handleNavToggle = this.handleNavToggle.bind(this);
    this.handleConfigErrorClose = this.handleConfigErrorClose.bind(this);
  }

  async componentDidMount() {
    await this.loadConfig();
  }

  // eslint-disable-next-line class-methods-use-this
  async handleLogout() {
    const { history } = this.props;
    await RootAPI.logout();
    history.replace('/login');
  }

  handleAboutOpen() {
    this.setState({ isAboutModalOpen: true });
  }

  handleAboutClose() {
    this.setState({ isAboutModalOpen: false });
  }

  handleNavToggle() {
    this.setState(({ isNavOpen }) => ({ isNavOpen: !isNavOpen }));
  }

  handleConfigErrorClose() {
    this.setState({
      configError: null,
    });
  }

  async loadConfig() {
    try {
      const [configRes, meRes] = await Promise.all([
        ConfigAPI.read(),
        MeAPI.read(),
      ]);
      const {
        data: { ansible_version, custom_virtualenvs, version },
      } = configRes;
      const {
        data: {
          results: [me],
        },
      } = meRes;

      this.setState({ ansible_version, custom_virtualenvs, version, me });
    } catch (err) {
      this.setState({ configError: err });
    }
  }

  render() {
    const {
      ansible_version,
      custom_virtualenvs,
      isAboutModalOpen,
      isNavOpen,
      me,
      version,
      configError,
    } = this.state;
    const {
      i18n,
      render = () => {},
      routeGroups = [],
      navLabel = '',
    } = this.props;

    const header = (
      <PageHeader
        showNavToggle
        onNavToggle={this.handleNavToggle}
        logo={<BrandLogo />}
        logoProps={{ href: '/' }}
        toolbar={
          <PageHeaderToolbar
            loggedInUser={me}
            isAboutDisabled={!version}
            onAboutClick={this.handleAboutOpen}
            onLogoutClick={this.handleLogout}
          />
        }
      />
    );

    const sidebar = (
      <PageSidebar
        isNavOpen={isNavOpen}
        nav={
          <Nav aria-label={navLabel}>
            <NavList>
              {routeGroups.map(({ groupId, groupTitle, routes }) => (
                <NavExpandableGroup
                  key={groupId}
                  groupId={groupId}
                  groupTitle={groupTitle}
                  routes={routes}
                />
              ))}
            </NavList>
          </Nav>
        }
      />
    );

    return (
      <Fragment>
        <Page usecondensed="True" header={header} sidebar={sidebar}>
          <ConfigProvider
            value={{ ansible_version, custom_virtualenvs, me, version }}
          >
            {render({ routeGroups })}
          </ConfigProvider>
        </Page>
        <About
          ansible_version={ansible_version}
          version={version}
          isOpen={isAboutModalOpen}
          onClose={this.handleAboutClose}
        />
        <AlertModal
          isOpen={configError}
          variant="danger"
          title={i18n._(t`Error!`)}
          onClose={this.handleConfigErrorClose}
        >
          {i18n._(t`Failed to retrieve configuration.`)}
          <ErrorDetail error={configError} />
        </AlertModal>
      </Fragment>
    );
  }
}

export { App as _App };
export default withI18n()(withRouter(App));
