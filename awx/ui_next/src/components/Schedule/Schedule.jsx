import React, { useEffect, useState } from 'react';
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

function Schedule({ i18n, setBreadcrumb, unifiedJobTemplate }) {
  const [schedule, setSchedule] = useState(null);
  const [contentLoading, setContentLoading] = useState(true);
  const [contentError, setContentError] = useState(null);
  const { scheduleId } = useParams();
  const location = useLocation();
  const { pathname } = location;
  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  useEffect(() => {
    const loadData = async () => {
      try {
        const { data } = await SchedulesAPI.readDetail(scheduleId);
        setSchedule(data);
      } catch (err) {
        setContentError(err);
      } finally {
        setContentLoading(false);
      }
    };

    loadData();
  }, [location.pathname, scheduleId]);

  useEffect(() => {
    if (schedule) {
      setBreadcrumb(unifiedJobTemplate, schedule);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [schedule, unifiedJobTemplate]);
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
    schedule.summary_fields.unified_job_template.id !==
    parseInt(unifiedJobTemplate.id, 10)
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

  if (
    !location.pathname.includes('schedules/') ||
    location.pathname.endsWith('edit')
  ) {
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
            <ScheduleEdit schedule={schedule} />
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
            {unifiedJobTemplate && (
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
