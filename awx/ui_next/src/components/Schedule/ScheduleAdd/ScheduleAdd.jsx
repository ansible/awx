import React, { useState } from 'react';
import { func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { useHistory, useLocation } from 'react-router-dom';
import { RRule } from 'rrule';
import { Card } from '@patternfly/react-core';
import { CardBody } from '../../Card';
import buildRuleObj from '../shared/buildRuleObj';
import ScheduleForm from '../shared/ScheduleForm';

function ScheduleAdd({ i18n, resource, apiModel }) {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();
  const location = useLocation();
  const { pathname } = location;
  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  const handleSubmit = async values => {
    try {
      const rule = new RRule(buildRuleObj(values, i18n));

      const { id: scheduleId } = await apiModel.createSchedule(resource.id, {
        rrule: rule.toString().replace(/\n/g, ' '),
      });

      history.push(`${pathRoot}schedules/${scheduleId}`);
    } catch (err) {
      setFormSubmitError(err);
    }
  };

  return (
    <Card>
      <CardBody>
        <ScheduleForm
          handleCancel={() => history.push(`${pathRoot}schedules`)}
          handleSubmit={handleSubmit}
          submitError={formSubmitError}
        />
      </CardBody>
    </Card>
  );
}

ScheduleAdd.propTypes = {
  apiModel: shape({ createSchedule: func.isRequired }).isRequired,
};

ScheduleAdd.defaultProps = {};

export default withI18n()(ScheduleAdd);
