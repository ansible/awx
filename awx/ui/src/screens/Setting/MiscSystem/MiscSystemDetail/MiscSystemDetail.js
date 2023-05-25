import React, { useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { CardBody, CardActionsRow } from 'components/Card';
import CodeDetail from 'components/DetailList/CodeDetail';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { DetailList } from 'components/DetailList';
import RoutedTabs from 'components/RoutedTabs';
import { SettingsAPI, ExecutionEnvironmentsAPI } from 'api';
import useRequest from 'hooks/useRequest';
import { useConfig } from 'contexts/Config';
import { useSettings } from 'contexts/Settings';
import { SettingDetail } from '../../shared';
import {
  formatJson,
  pluck,
  sortNestedDetails,
} from '../../shared/settingUtils';

function MiscSystemDetail() {
  const { me } = useConfig();
  const { GET: options } = useSettings();

  const {
    isLoading,
    error,
    request,
    result: system,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('system');
      if (data.DEFAULT_EXECUTION_ENVIRONMENT) {
        const {
          data: { name },
        } = await ExecutionEnvironmentsAPI.readDetail(
          data.DEFAULT_EXECUTION_ENVIRONMENT
        );
        data.DEFAULT_EXECUTION_ENVIRONMENT = name;
      }
      const systemData = pluck(
        data,
        'ACTIVITY_STREAM_ENABLED',
        'ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC',
        'AUTOMATION_ANALYTICS_GATHER_INTERVAL',
        'AUTOMATION_ANALYTICS_URL',
        'INSIGHTS_TRACKING_STATE',
        'MANAGE_ORGANIZATION_AUTH',
        'ORG_ADMINS_CAN_SEE_ALL_USERS',
        'REDHAT_USERNAME',
        'REDHAT_PASSWORD',
        'SUBSCRIPTIONS_USERNAME',
        'SUBSCRIPTIONS_PASSWORD',
        'INSTALL_UUID',
        'REMOTE_HOST_HEADERS',
        'TOWER_URL_BASE',
        'DEFAULT_EXECUTION_ENVIRONMENT',
        'PROXY_IP_ALLOWED_LIST',
        'AUTOMATION_ANALYTICS_LAST_GATHER',
        'AUTOMATION_ANALYTICS_LAST_ENTRIES',
        'UI_NEXT'
      );

      const mergedData = {};
      Object.keys(systemData).forEach((key) => {
        mergedData[key] = options[key];

        if (key === 'AUTOMATION_ANALYTICS_LAST_ENTRIES') {
          mergedData[key].value = formatJson(systemData[key]) ?? '';
        } else {
          mergedData[key].value = systemData[key];
        }
      });
      return sortNestedDetails(mergedData);
    }, [options]),
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

  // Display this detail in a code editor for readability
  if (options?.AUTOMATION_ANALYTICS_LAST_ENTRIES) {
    options.AUTOMATION_ANALYTICS_LAST_ENTRIES.type = 'nested object';
  }

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        {isLoading && <ContentLoading />}
        {!isLoading && error && <ContentError error={error} />}
        {!isLoading && system && (
          <DetailList>
            {system.map(([key, detail]) => {
              if (key === 'AUTOMATION_ANALYTICS_LAST_ENTRIES') {
                return (
                  <CodeDetail
                    key={key}
                    dataCy={key}
                    helpText={detail?.help_text}
                    label={detail?.label}
                    mode="javascript"
                    rows={4}
                    value={
                      detail?.value
                        ? JSON.stringify(detail.value, undefined, 2)
                        : ''
                    }
                  />
                );
              }
              return (
                <SettingDetail
                  key={key}
                  id={key}
                  helpText={detail?.help_text}
                  label={detail?.label}
                  type={detail?.type}
                  unit={detail?.unit}
                  value={detail?.value}
                />
              );
            })}
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
