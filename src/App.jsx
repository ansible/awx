import React, { Component, Fragment } from 'react';
import { global_breakpoint_md } from '@patternfly/react-tokens';
import {
  Nav,
  NavList,
  Page,
  PageHeader,
  PageSidebar,
  Button
} from '@patternfly/react-core';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { RootDialog } from './contexts/RootDialog';
import { withNetwork } from './contexts/Network';
import { Config } from './contexts/Config';

import AlertModal from './components/AlertModal';
import About from './components/About';
import NavExpandableGroup from './components/NavExpandableGroup';
import TowerLogo from './components/TowerLogo';
import PageHeaderToolbar from './components/PageHeaderToolbar';

class App extends Component {
  constructor (props) {
    super(props);

    // initialize with a closed navbar if window size is small
    const isNavOpen = typeof window !== 'undefined'
      && window.innerWidth >= parseInt(global_breakpoint_md.value, 10);

    this.state = {
      isAboutModalOpen: false,
      isNavOpen
    };

    this.onLogout = this.onLogout.bind(this);
    this.onAboutModalClose = this.onAboutModalClose.bind(this);
    this.onAboutModalOpen = this.onAboutModalOpen.bind(this);
    this.onNavToggle = this.onNavToggle.bind(this);
  }

  async onLogout () {
    const { api, handleHttpError } = this.props;
    try {
      await api.logout();
      window.location.replace('/#/login');
    } catch (err) {
      handleHttpError(err);
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

  render () {
    const { isAboutModalOpen, isNavOpen } = this.state;

    const { render, routeGroups = [], navLabel = '', i18n } = this.props;

    return (
      <Config>
        {({ ansible_version, version, me }) => (
          <RootDialog>
            {({
              title,
              bodyText,
              variant = 'info',
              clearRootDialogMessage
            }) => (
              <Fragment>
                {(title || bodyText) && (
                  <AlertModal
                    variant={variant}
                    isOpen={!!(title || bodyText)}
                    onClose={clearRootDialogMessage}
                    title={title}
                    actions={[
                      <Button
                        key="close"
                        variant="secondary"
                        onClick={clearRootDialogMessage}
                      >
                        {i18n._(t`Close`)}
                      </Button>
                    ]}
                  >
                    {bodyText}
                  </AlertModal>
                )}
                <Page
                  usecondensed="True"
                  header={(
                    <PageHeader
                      showNavToggle
                      onNavToggle={this.onNavToggle}
                      logo={<TowerLogo linkTo="/" />}
                      toolbar={(
                        <PageHeaderToolbar
                          loggedInUser={me}
                          isAboutDisabled={!version}
                          onAboutClick={this.onAboutModalOpen}
                          onLogoutClick={this.onLogout}
                        />
                      )}
                    />
                  )}
                  sidebar={(
                    <PageSidebar
                      isNavOpen={isNavOpen}
                      nav={(
                        <Nav aria-label={navLabel}>
                          <NavList>
                            {routeGroups.map(
                              ({ groupId, groupTitle, routes }) => (
                                <NavExpandableGroup
                                  key={groupId}
                                  groupId={groupId}
                                  groupTitle={groupTitle}
                                  routes={routes}
                                />
                              )
                            )}
                          </NavList>
                        </Nav>
                      )}
                    />
                  )}
                >
                  {render && render({ routeGroups })}
                </Page>
                <About
                  ansible_version={ansible_version}
                  version={version}
                  isOpen={isAboutModalOpen}
                  onClose={this.onAboutModalClose}
                />
              </Fragment>
            )}
          </RootDialog>
        )}
      </Config>
    );
  }
}

export { App as _App };
export default withI18n()(withNetwork(App));
