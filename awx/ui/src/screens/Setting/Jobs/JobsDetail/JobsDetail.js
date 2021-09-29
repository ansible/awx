import React, { useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { CardBody, CardActionsRow } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { DetailList } from 'components/DetailList';
import RoutedTabs from 'components/RoutedTabs';
import useRequest from 'hooks/useRequest';
import { useConfig } from 'contexts/Config';
import { useSettings } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import { sortNestedDetails } from '../../shared/settingUtils';
import { SettingDetail } from '../../shared';

function JobsDetail() {
  const { me } = useConfig();
  const { GET: options } = useSettings();

  const {
    isLoading,
    error,
    request,
    result: jobs,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('jobs');

      const {
        STDOUT_MAX_BYTES_DISPLAY,
        EVENT_STDOUT_MAX_BYTES_DISPLAY,
        ...jobsData
      } = data;

      const mergedData = {};
      Object.keys(jobsData).forEach((key) => {
        mergedData[key] = options[key];
        mergedData[key].value = jobsData[key];
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
      link: `/settings/jobs/details`,
      id: 0,
    },
  ];

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
      <CardBody>
        {isLoading && <ContentLoading />}
        {!isLoading && error && <ContentError error={error} />}
        {!isLoading && jobs && (
          <DetailList>
            {jobs.map(([key, detail]) => (
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
              ouiaId="jobs-detail-edit-button"
              aria-label={t`Edit`}
              component={Link}
              to="/settings/jobs/edit"
            >
              {t`Edit`}
            </Button>
          </CardActionsRow>
        )}
      </CardBody>
    </>
  );
}

export default JobsDetail;
