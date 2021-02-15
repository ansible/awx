import React from 'react';
import { withI18n } from '@lingui/react';
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
}) {
  const match = useRouteMatch();

  return (
    <Switch>
      <Route path={`${match.path}/add`}>
        <ScheduleAdd
          apiModel={apiModel}
          resource={resource}
          launchConfig={launchConfig}
          surveyConfig={surveyConfig}
        />
      </Route>
      <Route key="details" path={`${match.path}/:scheduleId`}>
        <Schedule
          setBreadcrumb={setBreadcrumb}
          resource={resource}
          launchConfig={launchConfig}
          surveyConfig={surveyConfig}
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
export default withI18n()(Schedules);
