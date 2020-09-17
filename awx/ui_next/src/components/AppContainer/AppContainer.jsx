import React, { useEffect, useState, useCallback } from 'react';
import { useHistory, useLocation, withRouter } from 'react-router-dom';
import {
  Nav,
  NavList,
  Page,
  PageHeader as PFPageHeader,
  PageSidebar,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import styled from 'styled-components';

import { ConfigAPI, MeAPI, RootAPI } from '../../api';
import { ConfigProvider } from '../../contexts/Config';
import About from '../About';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import BrandLogo from './BrandLogo';
import NavExpandableGroup from './NavExpandableGroup';
import PageHeaderToolbar from './PageHeaderToolbar';

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

function AppContainer({ i18n, navRouteConfig = [], children }) {
  const history = useHistory();
  const { pathname } = useLocation();
  const [config, setConfig] = useState({});
  const [configError, setConfigError] = useState(null);
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);
  const [isReady, setIsReady] = useState(false);

  const handleAboutModalOpen = () => setIsAboutModalOpen(true);
  const handleAboutModalClose = () => setIsAboutModalOpen(false);
  const handleConfigErrorClose = () => setConfigError(null);

  const handleLogout = useCallback(async () => {
    await RootAPI.logout();
    history.replace('/login');
  }, [history]);

  useEffect(() => {
    const loadConfig = async () => {
      if (config?.version) return;
      try {
        const [
          { data },
          {
            data: {
              results: [me],
            },
          },
        ] = await Promise.all([ConfigAPI.read(), MeAPI.read()]);
        setConfig({ ...data, me });
        setIsReady(true);
      } catch (err) {
        if (err.response.status === 401) {
          handleLogout();
          return;
        }
        setConfigError(err);
      }
    };
    loadConfig();
  }, [config, pathname, handleLogout]);

  const header = (
    <PageHeader
      showNavToggle
      logo={<BrandLogo />}
      logoProps={{ href: '/' }}
      headerTools={
        <PageHeaderToolbar
          loggedInUser={config?.me}
          isAboutDisabled={!config?.version}
          onAboutClick={handleAboutModalOpen}
          onLogoutClick={handleLogout}
        />
      }
    />
  );

  const sidebar = (
    <PageSidebar
      theme="dark"
      nav={
        <Nav aria-label={i18n._(t`Navigation`)} theme="dark">
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
      <Page isManagedSidebar header={header} sidebar={sidebar}>
        {isReady && <ConfigProvider value={config}>{children}</ConfigProvider>}
      </Page>
      <About
        ansible_version={config?.ansible_version}
        version={config?.version}
        isOpen={isAboutModalOpen}
        onClose={handleAboutModalClose}
      />
      <AlertModal
        isOpen={configError}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={handleConfigErrorClose}
      >
        {i18n._(t`Failed to retrieve configuration.`)}
        <ErrorDetail error={configError} />
      </AlertModal>
    </>
  );
}

export { AppContainer as _AppContainer };
export default withI18n()(withRouter(AppContainer));
