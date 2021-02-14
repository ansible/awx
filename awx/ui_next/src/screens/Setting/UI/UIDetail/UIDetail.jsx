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
import { pluck } from '../../shared/settingUtils';
import { SettingDetail } from '../../shared';

function UIDetail({ i18n }) {
  const { me } = useConfig();
  const { GET: options } = useSettings();

  const { isLoading, error, request, result: ui } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('ui');

      const uiData = pluck(
        data,
        'PENDO_TRACKING_STATE',
        'CUSTOM_LOGO',
        'CUSTOM_LOGIN_INFO'
      );

      return uiData;
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
      link: `/settings/ui/details`,
      id: 0,
    },
  ];

  // Change CUSTOM_LOGO type from string to image
  // to help SettingDetail render it as an <img>
  if (options?.CUSTOM_LOGO) {
    options.CUSTOM_LOGO.type = 'image';
  }

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        {isLoading && <ContentLoading />}
        {!isLoading && error && <ContentError error={error} />}
        {!isLoading && ui && (
          <DetailList>
            {Object.keys(ui).map(key => {
              const record = options?.[key];
              return (
                <SettingDetail
                  key={key}
                  id={key}
                  helpText={record?.help_text}
                  label={record?.label}
                  type={record?.type}
                  unit={record?.unit}
                  value={ui?.[key]}
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
              to="/settings/ui/edit"
              ouiaId="edit-button"
            >
              {i18n._(t`Edit`)}
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default withI18n()(UIDetail);
