import React, { useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { CardBody, CardActionsRow } from 'components/Card';
import ContentLoading from 'components/ContentLoading';
import ContentError from 'components/ContentError';
import { DetailList } from 'components/DetailList';
import RoutedTabs from 'components/RoutedTabs';
import { useConfig } from 'contexts/Config';
import { useSettings } from 'contexts/Settings';
import useRequest from 'hooks/useRequest';
import { SettingsAPI } from 'api';
import { SettingDetail } from '../../shared';

function MiscAuthenticationDetail() {
  const { me } = useConfig();
  const { GET: options } = useSettings();

  const {
    isLoading,
    error,
    request,
    result: authentication,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('authentication');
      return data;
    }, []),
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
      link: `/settings/miscellaneous_authentication/details`,
      id: 0,
    },
  ];

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        {isLoading && <ContentLoading />}
        {!isLoading && error && <ContentError error={error} />}
        {!isLoading && authentication && (
          <DetailList>
            {Object.keys(authentication).map((key) => {
              const record = options?.[key];
              return (
                <SettingDetail
                  key={key}
                  id={key}
                  helpText={record?.help_text}
                  label={record?.label}
                  type={record?.type}
                  unit={record?.unit}
                  value={authentication?.[key]}
                />
              );
            })}
          </DetailList>
        )}
        {me?.is_superuser && (
          <CardActionsRow>
            <Button
              ouiaId="authentication-detail-edit-button"
              aria-label={t`Edit`}
              component={Link}
              to="/settings/miscellaneous_authentication/edit"
            >
              {t`Edit`}
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default MiscAuthenticationDetail;
