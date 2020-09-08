import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useHistory, useLocation, withRouter } from 'react-router-dom';
import {
  Button,
  Nav,
  NavList,
  Page,
  PageHeader as PFPageHeader,
  PageSidebar,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import styled from 'styled-components';

import { ConfigAPI, MeAPI, OrganizationsAPI, RootAPI } from '../../api';
import { ConfigProvider } from '../../contexts/Config';
import { SESSION_TIMEOUT_KEY } from '../../constants';
import { isAuthenticated } from '../../util/auth';
import About from '../About';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import BrandLogo from './BrandLogo';
import NavExpandableGroup from './NavExpandableGroup';
import PageHeaderToolbar from './PageHeaderToolbar';

// The maximum supported timeout for setTimeout(), in milliseconds,
// is the highest number you can represent as a signed 32bit
// integer (approximately 25 days)
const MAX_TIMEOUT = 2 ** (32 - 1) - 1;

// The number of seconds the session timeout warning is displayed
// before the user is logged out. Increasing this number (up to
// the total session time, which is 1800s by default) will cause
// the session timeout warning to display sooner.
const SESSION_WARNING_DURATION = 10;

const PageHeader = styled(PFPageHeader)`
  & .pf-c-page__header-brand-link {
    color: inherit;

    &:hover {
      color: inherit;
    }
  }
`;

/**
 * The useStorage hook integrates with the browser's localStorage api.
 * It accepts a storage key as its only argument and returns a state
 * variable and setter function for that state variable.
 *
 * This utility behaves much like the standard useState hook with some
 * key differences:
 *   1. You don't pass it an initial value. Instead, the provided key
 *      is used to retrieve the initial value from local storage. If
 *      the key doesn't exist in local storage, null is returned.
 *   2. Behind the scenes, this hook registers an event listener with
 *      the Web Storage api to establish a two-way binding between the
 *      state variable and its corresponding local storage value. This
 *      means that updates to the state variable with the setter
 *      function will produce a corresponding update to the local
 *      storage value and vice-versa.
 *   3. When local storage is shared across browser tabs, the data
 *      binding is also shared across browser tabs. This means that
 *      updates to the state variable using the setter function on
 *      one tab will also update the state variable on any other tab
 *      using this hook with the same key and vice-versa.
 */
function useStorage(key) {
  const [storageVal, setStorageVal] = useState(
    window.localStorage.getItem(key)
  );
  window.addEventListener('storage', () => {
    const newVal = window.localStorage.getItem(key);
    if (newVal !== storageVal) {
      setStorageVal(newVal);
    }
  });
  const setValue = val => {
    window.localStorage.setItem(key, val);
    setStorageVal(val);
  };
  return [storageVal, setValue];
}

function AppContainer({ i18n, navRouteConfig = [], children }) {
  const history = useHistory();
  const { pathname } = useLocation();
  const [config, setConfig] = useState({});
  const [configError, setConfigError] = useState(null);
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);
  const [isReady, setIsReady] = useState(false);

  const sessionTimeoutId = useRef();
  const sessionIntervalId = useRef();
  const [sessionTimeout, setSessionTimeout] = useStorage(SESSION_TIMEOUT_KEY);
  const [timeoutWarning, setTimeoutWarning] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(null);

  const handleAboutModalOpen = () => setIsAboutModalOpen(true);
  const handleAboutModalClose = () => setIsAboutModalOpen(false);
  const handleConfigErrorClose = () => setConfigError(null);
  const handleSessionTimeout = () => setTimeoutWarning(true);

  const handleLogout = useCallback(async () => {
    await RootAPI.logout();
    setSessionTimeout(null);
  }, [setSessionTimeout]);

  const handleSessionContinue = () => {
    MeAPI.read();
    setTimeoutWarning(false);
  };

  useEffect(() => {
    if (!isAuthenticated(document.cookie)) history.replace('/login');
    const calcRemaining = () =>
      parseInt(sessionTimeout, 10) - new Date().getTime();
    const updateRemaining = () => setTimeRemaining(calcRemaining());
    setTimeoutWarning(false);
    clearTimeout(sessionTimeoutId.current);
    clearInterval(sessionIntervalId.current);
    sessionTimeoutId.current = setTimeout(
      handleSessionTimeout,
      Math.min(calcRemaining() - SESSION_WARNING_DURATION * 1000, MAX_TIMEOUT)
    );
    sessionIntervalId.current = setInterval(updateRemaining, 1000);
    return () => {
      clearTimeout(sessionTimeoutId.current);
      clearInterval(sessionIntervalId.current);
    };
  }, [history, sessionTimeout]);

  useEffect(() => {
    if (timeRemaining !== null && timeRemaining <= 1) {
      handleLogout();
    }
  }, [handleLogout, timeRemaining]);

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
          {
            data: { results: notificationAdminResults },
          },
        ] = await Promise.all([
          ConfigAPI.read(),
          MeAPI.read(),
          OrganizationsAPI.read({
            page_size: 1,
            role_level: 'notification_admin_role',
          }),
        ]);
        setConfig({
          ...data,
          me,
          isNotificationAdmin: Boolean(notificationAdminResults?.length),
        });
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
      <AlertModal
        title={i18n._(t`Your session is about to expire`)}
        isOpen={timeoutWarning && sessionTimeout > 0 && timeRemaining !== null}
        onClose={handleLogout}
        showClose={false}
        variant="warning"
        actions={[
          <Button
            key="confirm"
            variant="primary"
            onClick={handleSessionContinue}
          >
            {i18n._(t`Continue`)}
          </Button>,
          <Button key="logout" variant="secondary" onClick={handleLogout}>
            {i18n._(t`Logout`)}
          </Button>,
        ]}
      >
        {i18n._(
          t`You will be logged out in ${Number(
            Math.max(Math.floor(timeRemaining / 1000), 0)
          )} seconds due to inactivity.`
        )}
      </AlertModal>
    </>
  );
}

export { AppContainer as _AppContainer };
export default withI18n()(withRouter(AppContainer));
