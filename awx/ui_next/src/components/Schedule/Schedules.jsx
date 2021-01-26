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
  resource,
}) {
  const match = useRouteMatch();

  return (
    <Switch>
      <Route path={`${match.path}/add`}>
        <ScheduleAdd apiModel={apiModel} resource={resource} />
      </Route>
      <Route key="details" path={`${match.path}/:scheduleId`}>
        <Schedule setBreadcrumb={setBreadcrumb} resource={resource} />
      </Route>
      <Route key="list" path={`${match.path}`}>
        <ScheduleList
          loadSchedules={loadSchedules}
          loadScheduleOptions={loadScheduleOptions}
        />
      </Route>
    </Switch>
  );
}

export { Schedules as _Schedules };
export default withI18n()(Schedules);
