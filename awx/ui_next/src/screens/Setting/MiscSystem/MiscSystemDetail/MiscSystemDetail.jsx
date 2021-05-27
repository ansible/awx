import React, { useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { CardBody, CardActionsRow } from '../../../../components/Card';
import ContentError from '../../../../components/ContentError';
import ContentLoading from '../../../../components/ContentLoading';
import { DetailList } from '../../../../components/DetailList';
import RoutedTabs from '../../../../components/RoutedTabs';
import { SettingsAPI, ExecutionEnvironmentsAPI } from '../../../../api';
import useRequest from '../../../../util/useRequest';
import { useConfig } from '../../../../contexts/Config';
import { useSettings } from '../../../../contexts/Settings';
import { SettingDetail } from '../../shared';
import { sortNestedDetails, pluck } from '../../shared/settingUtils';

function MiscSystemDetail() {
  const { me } = useConfig();
  const { GET: allOptions } = useSettings();

  const { isLoading, error, request, result: system } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('all');
      let DEFAULT_EXECUTION_ENVIRONMENT = '';
      if (data.DEFAULT_EXECUTION_ENVIRONMENT) {
        const {
          data: { name },
        } = await ExecutionEnvironmentsAPI.readDetail(
          data.DEFAULT_EXECUTION_ENVIRONMENT
        );
        DEFAULT_EXECUTION_ENVIRONMENT = name;
      }
      const {
        OAUTH2_PROVIDER: {
          ACCESS_TOKEN_EXPIRE_SECONDS,
          REFRESH_TOKEN_EXPIRE_SECONDS,
          AUTHORIZATION_CODE_EXPIRE_SECONDS,
        },
        ...pluckedSystemData
      } = pluck(
        data,
        'ALLOW_OAUTH2_FOR_EXTERNAL_USERS',
        'AUTH_BASIC_ENABLED',
        'AUTOMATION_ANALYTICS_GATHER_INTERVAL',
        'AUTOMATION_ANALYTICS_URL',
        'INSIGHTS_TRACKING_STATE',
        'LOGIN_REDIRECT_OVERRIDE',
        'MANAGE_ORGANIZATION_AUTH',
        'DISABLE_LOCAL_AUTH',
        'OAUTH2_PROVIDER',
        'ORG_ADMINS_CAN_SEE_ALL_USERS',
        'REDHAT_PASSWORD',
        'REDHAT_USERNAME',
        'REMOTE_HOST_HEADERS',
        'SESSIONS_PER_USER',
        'SESSION_COOKIE_AGE',
        'SUBSCRIPTIONS_USERNAME',
        'SUBSCRIPTIONS_PASSWORD',
        'TOWER_URL_BASE'
      );
      const systemData = {
        ...pluckedSystemData,
        ACCESS_TOKEN_EXPIRE_SECONDS,
        REFRESH_TOKEN_EXPIRE_SECONDS,
        AUTHORIZATION_CODE_EXPIRE_SECONDS,
        DEFAULT_EXECUTION_ENVIRONMENT,
      };
      const {
        OAUTH2_PROVIDER: OAUTH2_PROVIDER_OPTIONS,
        ...options
      } = allOptions;
      const systemOptions = {
        ...options,
        ACCESS_TOKEN_EXPIRE_SECONDS: {
          ...OAUTH2_PROVIDER_OPTIONS,
          type: OAUTH2_PROVIDER_OPTIONS.child.type,
          label: t`Access Token Expiration`,
        },
        REFRESH_TOKEN_EXPIRE_SECONDS: {
          ...OAUTH2_PROVIDER_OPTIONS,
          type: OAUTH2_PROVIDER_OPTIONS.child.type,
          label: t`Refresh Token Expiration`,
        },
        AUTHORIZATION_CODE_EXPIRE_SECONDS: {
          ...OAUTH2_PROVIDER_OPTIONS,
          type: OAUTH2_PROVIDER_OPTIONS.child.type,
          label: t`Authorization Code Expiration`,
        },
      };
      const mergedData = {};
      Object.keys(systemData).forEach(key => {
        mergedData[key] = systemOptions[key];
        mergedData[key].value = systemData[key];
      });
      return sortNestedDetails(mergedData);
    }, [allOptions]),
    null
  );

  useEffect(() => {
    request();
  }, [request]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Settings`}
        </>
      ),
      link: `/settings`,
      id: 99,
    },
    {
      name: t`Details`,
      link: `/settings/miscellaneous_system/details`,
      id: 0,
    },
  ];

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        {isLoading && <ContentLoading />}
        {!isLoading && error && <ContentError error={error} />}
        {!isLoading && system && (
          <DetailList>
            {system.map(([key, detail]) => (
              <SettingDetail
                key={key}
                id={key}
                helpText={detail?.help_text}
                label={detail?.label}
                type={detail?.type}
                unit={detail?.unit}
                value={detail?.value}
              />
            ))}
          </DetailList>
        )}
        {me?.is_superuser && (
          <CardActionsRow>
            <Button
              ouiaId="system-detail-edit-button"
              aria-label={t`Edit`}
              component={Link}
              to="/settings/miscellaneous_system/edit"
            >
              {t`Edit`}
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default MiscSystemDetail;
