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

function GoogleOAuth2Detail({ i18n }) {
  const { me } = useConfig();
  const { GET: options } = useSettings();

  const { isLoading, error, request, result: googleOAuth2 } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('google-oauth2');
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
          {i18n._(t`Back to Settings`)}
        </>
      ),
      link: `/settings`,
      id: 99,
    },
    {
      name: i18n._(t`Details`),
      link: `/settings/google_oauth2/details`,
      id: 0,
    },
  ];

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        {isLoading && <ContentLoading />}
        {!isLoading && error && <ContentError error={error} />}
        {!isLoading && googleOAuth2 && (
          <DetailList>
            {Object.keys(googleOAuth2).map(key => {
              const record = options?.[key];
              return (
                <SettingDetail
                  key={key}
                  id={key}
                  helpText={record?.help_text}
                  label={record?.label}
                  type={record?.type}
                  unit={record?.unit}
                  value={googleOAuth2?.[key]}
                />
              );
            })}
          </DetailList>
        )}
        {me?.is_superuser && (
          <CardActionsRow>
            <Button
              aria-label={i18n._(t`Edit`)}
              component={Link}
              to="/settings/google_oauth2/edit"
            >
              {i18n._(t`Edit`)}
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default withI18n()(GoogleOAuth2Detail);
