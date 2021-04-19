import React, { useCallback, useContext, useEffect, useMemo } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { ConfigAPI, MeAPI, RootAPI } from '../api';
import useRequest, { useDismissableError } from '../util/useRequest';
import AlertModal from '../components/AlertModal';
import ErrorDetail from '../components/ErrorDetail';

// eslint-disable-next-line import/prefer-default-export
export const ConfigContext = React.createContext([{}, () => {}]);
ConfigContext.displayName = 'ConfigContext';

export const Config = ConfigContext.Consumer;
export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
};

export const ConfigProvider = withI18n()(({ i18n, children }) => {
  const { pathname } = useLocation();

  const {
    error: configError,
    isLoading,
    request,
    result: config,
    setValue: setConfig,
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
      return { ...data, me };
    }, []),
    {}
  );

  const { error, dismissError } = useDismissableError(configError);

  useEffect(() => {
    if (pathname !== '/login') {
      request();
    }
  }, [request, pathname]);

  useEffect(() => {
    if (error?.response?.status === 401) {
      RootAPI.logout();
    }
  }, [error]);

  const value = useMemo(() => ({ ...config, isLoading, setConfig }), [
    config,
    isLoading,
    setConfig,
  ]);

  return (
    <ConfigContext.Provider value={value}>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
          ouiaId="config-error-modal"
        >
          {i18n._(t`Failed to retrieve configuration.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
      {children}
    </ConfigContext.Provider>
  );
});

export const useAuthorizedPath = () => {
  const config = useConfig();
  const subscriptionMgmtRoute = useRouteMatch({
    path: '/subscription_management',
  });
  return !!config.license_info?.valid_key && !subscriptionMgmtRoute;
};
