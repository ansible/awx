import React from 'react';
import { Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { PageSection, Card } from '@patternfly/react-core';
import Breadcrumbs from '../../components/Breadcrumbs';
import { ScheduleList } from '../../components/Schedule';
import { SchedulesAPI } from '../../api';

function AllSchedules({ i18n }) {
  const loadScheduleOptions = () => {
    return SchedulesAPI.readOptions();
  };

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
              <ScheduleList
                loadSchedules={loadSchedules}
                loadScheduleOptions={loadScheduleOptions}
                hideAddButton
              />
            </Card>
          </PageSection>
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(AllSchedules);
