import React from 'react';
import { withI18n } from '@lingui/react';
import { Switch, Route, useRouteMatch } from 'react-router-dom';
import { Schedule, ScheduleAdd, ScheduleList } from '@components/Schedule';

function Schedules({
  createSchedule,
  loadScheduleOptions,
  loadSchedules,
  setBreadcrumb,
  unifiedJobTemplate,
}) {
  const match = useRouteMatch();

  return (
    <Switch>
      <Route
        path={`${match.path}/add`}
        render={() => <ScheduleAdd createSchedule={createSchedule} />}
      />
      <Route
        key="details"
        path={`${match.path}/:scheduleId`}
        render={() => (
          <Schedule
            unifiedJobTemplate={unifiedJobTemplate}
            setBreadcrumb={setBreadcrumb}
          />
        )}
      />
      <Route
        key="list"
        path={`${match.path}`}
        render={() => {
          return (
            <ScheduleList
              loadSchedules={loadSchedules}
              loadScheduleOptions={loadScheduleOptions}
            />
          );
        }}
      />
    </Switch>
  );
}

export { Schedules as _Schedules };
export default withI18n()(Schedules);
