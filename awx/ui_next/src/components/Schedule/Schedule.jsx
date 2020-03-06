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
import { CardActions } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { TabbedCardHeader } from '@components/Card';
import { ScheduleDetail } from '@components/Schedule';
import { SchedulesAPI } from '@api';

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
        setBreadcrumb(unifiedJobTemplate, data);
      } catch (err) {
        setContentError(err);
      } finally {
        setContentLoading(false);
      }
    };

    loadData();
  }, [location.pathname, scheduleId, unifiedJobTemplate, setBreadcrumb]);

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

  let cardHeader = null;
  if (
    location.pathname.includes('schedules/') &&
    !location.pathname.endsWith('edit')
  ) {
    cardHeader = (
      <TabbedCardHeader>
        <RoutedTabs tabsArray={tabsArray} />
        <CardActions>
          <CardCloseButton linkTo={`${pathRoot}schedules`} />
        </CardActions>
      </TabbedCardHeader>
    );
  }
  return (
    <>
      {cardHeader}
      <Switch>
        <Redirect
          from={`${pathRoot}schedules/:scheduleId`}
          to={`${pathRoot}schedules/:scheduleId/details`}
          exact
        />
        {schedule && [
          <Route
            key="details"
            path={`${pathRoot}schedules/:scheduleId/details`}
            render={() => {
              return <ScheduleDetail schedule={schedule} />;
            }}
          />,
        ]}
        <Route
          key="not-found"
          path="*"
          render={() => {
            return (
              <ContentError>
                {unifiedJobTemplate && (
                  <Link to={`${pathRoot}details`}>
                    {i18n._(t`View Details`)}
                  </Link>
                )}
              </ContentError>
            );
          }}
        />
      </Switch>
    </>
  );
}

export { Schedule as _Schedule };
export default withI18n()(Schedule);
