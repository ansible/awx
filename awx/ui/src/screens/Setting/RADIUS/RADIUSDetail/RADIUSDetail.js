import React, { useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Button, Alert as PFAlert } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { CardBody, CardActionsRow } from 'components/Card';
import ContentLoading from 'components/ContentLoading';
import ContentError from 'components/ContentError';
import RoutedTabs from 'components/RoutedTabs';
import { SettingsAPI } from 'api';
import useRequest from 'hooks/useRequest';
import { DetailList } from 'components/DetailList';
import { useConfig } from 'contexts/Config';
import { useSettings } from 'contexts/Settings';
import { SettingDetail } from '../../shared';

const Alert = styled(PFAlert)`
  margin-bottom: 20px;
`;

function RADIUSDetail() {
  const { me } = useConfig();
  const { GET: options } = useSettings();

  const {
    isLoading,
    error,
    request,
    result: radius,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('radius');
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
      link: `/settings/radius/details`,
      id: 0,
    },
  ];

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        {isLoading && <ContentLoading />}
        {!isLoading && error && <ContentError error={error} />}
        {!isLoading && radius && (
          <>
            <Alert
              variant="info"
              isInline
              data-cy="RADIUS-deprecation-warning"
              title={t`This feature is deprecated and will be removed in a future release.`}
              ouiaId="radius-deprecation-alert"
            />
            <DetailList>
              {Object.keys(radius).map((key) => {
                const record = options?.[key];
                return (
                  <SettingDetail
                    key={key}
                    id={key}
                    helpText={record?.help_text}
                    label={record?.label}
                    type={record?.type}
                    unit={record?.unit}
                    value={radius?.[key]}
                  />
                );
              })}
            </DetailList>
          </>
        )}
        {me?.is_superuser && (
          <CardActionsRow>
            <Button
              ouiaId="radius-detail-edit-button"
              aria-label={t`Edit`}
              component={Link}
              to="/settings/radius/edit"
            >
              {t`Edit`}
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default RADIUSDetail;
