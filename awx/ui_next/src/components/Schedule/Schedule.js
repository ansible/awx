import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';

import {
  Switch,
  Route,
  Link,
  Redirect,
  useLocation,
  useParams,
} from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { SchedulesAPI } from 'api';
import useRequest from 'hooks/useRequest';
import RoutedTabs from '../RoutedTabs';
import ContentError from '../ContentError';
import ContentLoading from '../ContentLoading';
import ScheduleDetail from './ScheduleDetail';
import ScheduleEdit from './ScheduleEdit';

function Schedule({
  setBreadcrumb,
  resource,
  launchConfig,
  surveyConfig,
  hasDaysToKeepField,
  resourceDefaultCredentials,
}) {
  const { scheduleId } = useParams();

  const { pathname } = useLocation();

  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  const {
    isLoading,
    error,
    request: loadData,
    result: schedule,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SchedulesAPI.readDetail(scheduleId);

      return data;
    }, [scheduleId]),
    null
  );

  useEffect(() => {
    loadData();
  }, [loadData, pathname]);

  useEffect(() => {
    if (schedule) {
      setBreadcrumb(resource, schedule);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [schedule, resource]);
  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Schedules`}
        </>
      ),
      link: `${pathRoot}schedules`,
      id: 99,
    },
    {
      name: t`Details`,
      link: `${pathRoot}schedules/${schedule && schedule.id}/details`,
      id: 0,
    },
  ];

  if (!isLoading && error) {
    return (
      <ContentError isNotFound error={error}>
        {error.response && error.response.status === 404 && (
          <span>
            {t`Schedule not found.`}{' '}
            <Link to={`${pathRoot}schedules`}>{t`View Schedules`}</Link>
          </span>
        )}
      </ContentError>
    );
  }

  if (isLoading || !schedule?.summary_fields?.unified_job_template?.id) {
    return <ContentLoading />;
  }

  if (
    schedule?.summary_fields.unified_job_template.id !==
    parseInt(resource.id, 10)
  ) {
    return (
      <ContentError>
        {schedule && (
          <Link to={`${pathRoot}schedules`}>{t`View Schedules`}</Link>
        )}
      </ContentError>
    );
  }

  if (error) {
    return <ContentError error={error} />;
  }

  let showCardHeader = true;

  if (!pathname.includes('schedules/') || pathname.endsWith('edit')) {
    showCardHeader = false;
  }

  return (
    <>
      {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
      <Switch>
        <Redirect
          from={`${pathRoot}schedules/:scheduleId`}
          to={`${pathRoot}schedules/:scheduleId/details`}
          exact
        />
        {schedule && [
          <Route key="edit" path={`${pathRoot}schedules/:id/edit`}>
            <ScheduleEdit
              hasDaysToKeepField={hasDaysToKeepField}
              schedule={schedule}
              resource={resource}
              launchConfig={launchConfig}
              surveyConfig={surveyConfig}
              resourceDefaultCredentials={resourceDefaultCredentials}
            />
          </Route>,
          <Route
            key="details"
            path={`${pathRoot}schedules/:scheduleId/details`}
          >
            <ScheduleDetail
              hasDaysToKeepField={hasDaysToKeepField}
              schedule={schedule}
              surveyConfig={surveyConfig}
            />
          </Route>,
        ]}
        <Route key="not-found" path="*">
          <ContentError>
            {resource && (
              <Link to={`${pathRoot}details`}>{t`View Details`}</Link>
            )}
          </ContentError>
        </Route>
      </Switch>
    </>
  );
}

export { Schedule as _Schedule };
export default Schedule;
