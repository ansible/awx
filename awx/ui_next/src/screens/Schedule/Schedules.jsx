import React from 'react';
import { Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import Breadcrumbs from '@components/Breadcrumbs';
import ScheduleList from '@components/ScheduleList';
import { SchedulesAPI } from '@api';
import { PageSection, Card } from '@patternfly/react-core';

function Schedules({ i18n }) {
  const loadSchedules = params => {
    return SchedulesAPI.read(params);
  };

  return (
    <>
      <Breadcrumbs
        breadcrumbConfig={{
          '/schedules': i18n._(t`Schedules`),
        }}
      />
      <Switch>
        <Route path="/schedules">
          <PageSection>
            <Card>
              <ScheduleList loadSchedules={loadSchedules} />
            </Card>
          </PageSection>
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(Schedules);
