import React from 'react';
import { Switch, Route, useRouteMatch } from 'react-router-dom';

import Schedule from './Schedule';
import ScheduleAdd from './ScheduleAdd';
import ScheduleList from './ScheduleList';

function Schedules({
  apiModel,
  loadScheduleOptions,
  loadSchedules,
  setBreadcrumb,
  launchConfig,
  surveyConfig,
  resource,
  resourceDefaultCredentials,
}) {
  const match = useRouteMatch();

  // For some management jobs that delete data, we want to provide an additional
  // field on the scheduler for configuring the number of days to retain.

  const hasDaysToKeepField = [
    'cleanup_activitystream',
    'cleanup_jobs',
  ].includes(resource?.job_type);

  return (
    <Switch>
      <Route path={`${match.path}/add`}>
        <ScheduleAdd
          hasDaysToKeepField={hasDaysToKeepField}
          apiModel={apiModel}
          resource={resource}
          launchConfig={launchConfig}
          surveyConfig={surveyConfig}
          resourceDefaultCredentials={resourceDefaultCredentials}
        />
      </Route>
      <Route key="details" path={`${match.path}/:scheduleId`}>
        <Schedule
          hasDaysToKeepField={hasDaysToKeepField}
          setBreadcrumb={setBreadcrumb}
          resource={resource}
          launchConfig={launchConfig}
          surveyConfig={surveyConfig}
          resourceDefaultCredentials={resourceDefaultCredentials}
        />
      </Route>
      <Route key="list" path={`${match.path}`}>
        <ScheduleList
          resource={resource}
          loadSchedules={loadSchedules}
          launchConfig={launchConfig}
          surveyConfig={surveyConfig}
          loadScheduleOptions={loadScheduleOptions}
        />
      </Route>
    </Switch>
  );
}

export { Schedules as _Schedules };
export default Schedules;
