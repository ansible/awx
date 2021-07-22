import React, { useCallback, useContext, useEffect, useMemo } from 'react';
import { useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';

import { ConfigAPI, MeAPI, UsersAPI, OrganizationsAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { useSession } from './Session';

// eslint-disable-next-line import/prefer-default-export
export const ConfigContext = React.createContext({});
ConfigContext.displayName = 'ConfigContext';

export const Config = ConfigContext.Consumer;
export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
};

export const ConfigProvider = ({ children }) => {
  const { logout } = useSession();

  const {
    error: configError,
    isLoading,
    request,
    result: config,
  } = useRequest(
    useCallback(async () => {
      const [
        { data },
        {
          data: {
            results: [me],
          },
        },
      ] = await Promise.all([ConfigAPI.read(), MeAPI.read()]);

      const [
        {
          data: { count: adminOrgCount },
        },
        {
          data: { count: notifAdminCount },
        },
        {
          data: { count: execEnvAdminCount },
        },
      ] = await Promise.all([
        UsersAPI.readAdminOfOrganizations(me?.id),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'execution_environment_admin_role',
        }),
      ]);

      return { ...data, me, adminOrgCount, notifAdminCount, execEnvAdminCount };
    }, []),
    { adminOrgCount: 0, notifAdminCount: 0, execEnvAdminCount: 0 }
  );

  const { error, dismissError } = useDismissableError(configError);

  useEffect(() => {
    request();
  }, [request]);

  useEffect(() => {
    if (error?.response?.status === 401) {
      logout();
    }
  }, [error, logout]);

  const value = useMemo(
    () => ({ ...config, request, isLoading }),
    [config, request, isLoading]
  );

  return (
    <ConfigContext.Provider value={value}>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
          ouiaId="config-error-modal"
        >
          {t`Failed to retrieve configuration.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
      {children}
    </ConfigContext.Provider>
  );
};

export const useUserProfile = () => {
  const config = useConfig();
  return {
    isSuperUser: !!config.me?.is_superuser,
    isSystemAuditor: !!config.me?.is_system_auditor,
    isOrgAdmin: config.adminOrgCount,
    isNotificationAdmin: config.notifAdminCount,
    isExecEnvAdmin: config.execEnvAdminCount,
  };
};

export const useAuthorizedPath = () => {
  const config = useConfig();
  const subscriptionMgmtRoute = useRouteMatch({
    path: '/subscription_management',
  });
  return !!config.license_info?.valid_key && !subscriptionMgmtRoute;
};
