import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import {
  Switch,
  Route,
  Link,
  Redirect,
  useLocation,
  useParams,
} from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import RoutedTabs from '../RoutedTabs';
import ContentError from '../ContentError';
import ContentLoading from '../ContentLoading';
import ScheduleDetail from './ScheduleDetail';
import ScheduleEdit from './ScheduleEdit';
import { SchedulesAPI } from '../../api';
import useRequest from '../../util/useRequest';

function Schedule({ i18n, setBreadcrumb, resource }) {
  const { scheduleId } = useParams();

  const { pathname } = useLocation();

  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  const {
    isLoading: contentLoading,
    error: contentError,
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
          {i18n._(t`Back to Schedules`)}
        </>
      ),
      link: `${pathRoot}schedules`,
      id: 99,
    },
    {
      name: i18n._(t`Details`),
      link: `${pathRoot}schedules/${schedule && schedule.id}/details`,
      id: 0,
    },
  ];

  if (contentLoading) {
    return <ContentLoading />;
  }

  if (
    schedule?.summary_fields.unified_job_template.id !==
    parseInt(resource.id, 10)
  ) {
    return (
      <ContentError>
        {schedule && (
          <Link to={`${pathRoot}schedules`}>{i18n._(t`View Schedules`)}</Link>
        )}
      </ContentError>
    );
  }

  if (contentError) {
    return <ContentError error={contentError} />;
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
            <ScheduleEdit schedule={schedule} resource={resource} />
          </Route>,
          <Route
            key="details"
            path={`${pathRoot}schedules/:scheduleId/details`}
          >
            <ScheduleDetail schedule={schedule} />
          </Route>,
        ]}
        <Route key="not-found" path="*">
          <ContentError>
            {resource && (
              <Link to={`${pathRoot}details`}>{i18n._(t`View Details`)}</Link>
            )}
          </ContentError>
        </Route>
      </Switch>
    </>
  );
}

export { Schedule as _Schedule };
export default withI18n()(Schedule);
