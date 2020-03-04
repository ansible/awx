import React from 'react';
import { withI18n } from '@lingui/react';

import { Switch, Route, withRouter } from 'react-router-dom';

import JobTemplateSchedule from '../JobTemplateSchedule/JobTemplateSchedule';

function JobTemplateSchedules({ setBreadcrumb, jobTemplate }) {
  return (
    <Switch>
      <Route
        key="details"
        path="/templates/job_template/:id/schedules/:scheduleId/"
        render={() => (
          <JobTemplateSchedule
            jobTemplate={jobTemplate}
            setBreadcrumb={setBreadcrumb}
          />
        )}
      />
    </Switch>
  );
}

export { JobTemplateSchedules as _JobTemplateSchedules };
export default withI18n()(withRouter(JobTemplateSchedules));
