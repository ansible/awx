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

function JobTemplateSchedule({ i18n, setBreadcrumb, jobTemplate }) {
  const [jobTemplateSchedule, setJobTemplateSchedule] = useState(null);
  const [contentLoading, setContentLoading] = useState(true);
  const [contentError, setContentError] = useState(null);
  const { id: jobTemplateId, scheduleId } = useParams();
  const location = useLocation();

  useEffect(() => {
    const loadData = async () => {
      try {
        const { data } = await SchedulesAPI.readDetail(scheduleId);
        setJobTemplateSchedule(data);
        setBreadcrumb(jobTemplate, data);
      } catch (err) {
        setContentError(err);
      } finally {
        setContentLoading(false);
      }
    };

    loadData();
  }, [location.pathname, scheduleId, jobTemplate, setBreadcrumb]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Schedules`)}
        </>
      ),
      link: `/templates/job_template/${jobTemplate.id}/schedules`,
      id: 99,
    },
    {
      name: i18n._(t`Details`),
      link: `/templates/job_template/${
        jobTemplate.id
      }/schedules/${jobTemplateSchedule && jobTemplateSchedule.id}/details`,
      id: 0,
    },
  ];

  if (contentLoading) {
    return <ContentLoading />;
  }

  if (
    jobTemplateSchedule.summary_fields.unified_job_template.id !==
    parseInt(jobTemplateId, 10)
  ) {
    return (
      <ContentError>
        {jobTemplateSchedule && (
          <Link to={`/templates/job_template/${jobTemplate.id}/schedules`}>
            {i18n._(t`View Template Schedules`)}
          </Link>
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
          <CardCloseButton
            linkTo={`/templates/job_template/${jobTemplate.id}/schedules`}
          />
        </CardActions>
      </TabbedCardHeader>
    );
  }
  return (
    <>
      {cardHeader}
      <Switch>
        <Redirect
          from="/templates/job_template/:id/schedules/:scheduleId"
          to="/templates/job_template/:id/schedules/:scheduleId/details"
          exact
        />
        {jobTemplateSchedule && [
          <Route
            key="details"
            path="/templates/job_template/:id/schedules/:scheduleId/details"
            render={() => {
              return <ScheduleDetail schedule={jobTemplateSchedule} />;
            }}
          />,
        ]}
        <Route
          key="not-found"
          path="*"
          render={() => {
            return (
              <ContentError>
                {jobTemplate && (
                  <Link
                    to={`/templates/job_template/${jobTemplate.id}/details`}
                  >
                    {i18n._(t`View Template Details`)}
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

export { JobTemplateSchedule as _JobTemplateSchedule };
export default withI18n()(JobTemplateSchedule);
