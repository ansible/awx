import React, { useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { CardBody, CardActionsRow } from '../../../../components/Card';
import ContentLoading from '../../../../components/ContentLoading';
import ContentError from '../../../../components/ContentError';
import RoutedTabs from '../../../../components/RoutedTabs';
import { SettingsAPI } from '../../../../api';
import useRequest from '../../../../util/useRequest';
import { DetailList } from '../../../../components/DetailList';
import { useConfig } from '../../../../contexts/Config';
import { useSettings } from '../../../../contexts/Settings';
import SettingDetail from '../../shared';
import { sortNestedDetails, pluck } from '../../shared/settingUtils';

function LoggingDetail({ i18n }) {
  const { me } = useConfig();
  const { GET: options } = useSettings();

  const { isLoading, error, request, result: logging } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('logging');

      const loggingData = pluck(
        data,
        'LOG_AGGREGATOR_ENABLED',
        'LOG_AGGREGATOR_HOST',
        'LOG_AGGREGATOR_INDIVIDUAL_FACTS',
        'LOG_AGGREGATOR_LEVEL',
        'LOG_AGGREGATOR_LOGGERS',
        'LOG_AGGREGATOR_PASSWORD',
        'LOG_AGGREGATOR_PORT',
        'LOG_AGGREGATOR_PROTOCOL',
        'LOG_AGGREGATOR_TCP_TIMEOUT',
        'LOG_AGGREGATOR_TYPE',
        'LOG_AGGREGATOR_USERNAME',
        'LOG_AGGREGATOR_VERIFY_CERT'
      );

      const mergedData = {};
      Object.keys(loggingData).forEach(key => {
        mergedData[key] = options[key];
        mergedData[key].value = loggingData[key];
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
          {i18n._(t`Back to Settings`)}
        </>
      ),
      link: `/settings`,
      id: 99,
    },
    {
      name: i18n._(t`Details`),
      link: `/settings/logging/details`,
      id: 0,
    },
  ];

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        {isLoading && <ContentLoading />}
        {!isLoading && error && <ContentError error={error} />}
        {!isLoading && logging && (
          <DetailList>
            {logging.map(([key, detail]) => (
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
              aria-label={i18n._(t`Edit`)}
              component={Link}
              to="/settings/logging/edit"
            >
              {i18n._(t`Edit`)}
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default withI18n()(LoggingDetail);
