import React, { useState, useEffect } from 'react';
import { withRouter } from 'react-router-dom';
import {
  Button,
  Nav,
  NavList,
  Page,
  PageHeader as PFPageHeader,
  PageHeaderTools,
  PageHeaderToolsGroup,
  PageHeaderToolsItem,
  PageSidebar,
} from '@patternfly/react-core';
import { t, Plural } from '@lingui/macro';

import styled from 'styled-components';

import { useConfig, useAuthorizedPath } from 'contexts/Config';
import { useSession } from 'contexts/Session';
import issuePendoIdentity from 'util/issuePendoIdentity';
import About from '../About';
import BrandLogo from './BrandLogo';
import NavExpandableGroup from './NavExpandableGroup';
import PageHeaderToolbar from './PageHeaderToolbar';
import AlertModal from '../AlertModal';

const PageHeader = styled(PFPageHeader)`
  & .pf-c-page__header-brand-link {
    color: inherit;
    &:hover {
      color: inherit;
    }
  }
`;

function AppContainer({ navRouteConfig = [], children }) {
  const config = useConfig();
  const { logout, handleSessionContinue, sessionCountdown } = useSession();

  const isReady = !!config.license_info;
  const isSidebarVisible = useAuthorizedPath();
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);

  const handleAboutModalOpen = () => setIsAboutModalOpen(true);
  const handleAboutModalClose = () => setIsAboutModalOpen(false);

  useEffect(() => {
    if ('analytics_status' in config) {
      issuePendoIdentity(config);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config.analytics_status]);

  const brandName = config?.license_info?.product_name;
  const alt = brandName ? t`${brandName} logo` : t`brand logo`;

  const header = (
    <PageHeader
      showNavToggle
      logo={<BrandLogo alt={alt} />}
      logoProps={{ href: '/' }}
      headerTools={
        <PageHeaderToolbar
          loggedInUser={config?.me}
          isAboutDisabled={!config?.version}
          onAboutClick={handleAboutModalOpen}
          onLogoutClick={logout}
        />
      }
    />
  );

  const simpleHeader = config.isLoading ? null : (
    <PageHeader
      logo={<BrandLogo alt={alt} />}
      headerTools={
        <PageHeaderTools>
          <PageHeaderToolsGroup>
            <PageHeaderToolsItem>
              <Button onClick={logout} variant="tertiary" ouiaId="logout">
                {t`Logout`}
              </Button>
            </PageHeaderToolsItem>
          </PageHeaderToolsGroup>
        </PageHeaderTools>
      }
    />
  );

  const sidebar = (
    <PageSidebar
      theme="dark"
      nav={
        <Nav
          aria-label={t`Navigation`}
          theme="dark"
          ouiaId="sidebar-navigation"
        >
          <NavList>
            {navRouteConfig.map(({ groupId, groupTitle, routes }) => (
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
    <>
      <Page
        isManagedSidebar={isSidebarVisible}
        header={isSidebarVisible ? header : simpleHeader}
        sidebar={isSidebarVisible && sidebar}
      >
        {isReady ? children : null}
      </Page>
      <About
        version={config?.version}
        isOpen={isAboutModalOpen}
        onClose={handleAboutModalClose}
      />
      <AlertModal
        ouiaId="session-expiration-modal"
        title={t`Your session is about to expire`}
        isOpen={sessionCountdown && sessionCountdown > 0}
        onClose={logout}
        showClose={false}
        variant="warning"
        actions={[
          <Button
            ouiaId="session-expiration-continue-button"
            key="confirm"
            variant="primary"
            onClick={handleSessionContinue}
          >
            {t`Continue`}
          </Button>,
          <Button
            ouiaId="session-expiration-logout-button"
            key="logout"
            variant="secondary"
            onClick={logout}
          >
            {t`Logout`}
          </Button>,
        ]}
      >
        <Plural
          value={sessionCountdown}
          one="You will be logged out in # second due to inactivity"
          other="You will be logged out in # seconds due to inactivity"
        />
      </AlertModal>
    </>
  );
}

export { AppContainer as _AppContainer };
export default withRouter(AppContainer);
