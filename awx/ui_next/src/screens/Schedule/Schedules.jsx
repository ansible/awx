import React from 'react';
import { Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import Breadcrumbs from '@components/Breadcrumbs';
import { ScheduleList } from './ScheduleList';

function Schedules({ i18n }) {
  return (
    <>
      <Breadcrumbs
        breadcrumbConfig={{
          '/schedules': i18n._(t`Schedules`),
        }}
      />
      <Switch>
        <Route path="/schedules">
          <ScheduleList />
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(Schedules);
