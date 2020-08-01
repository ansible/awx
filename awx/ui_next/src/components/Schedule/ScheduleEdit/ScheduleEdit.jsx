import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { useHistory, useLocation } from 'react-router-dom';
import { RRule } from 'rrule';
import { shape } from 'prop-types';
import { Card } from '@patternfly/react-core';
import { CardBody } from '../../Card';
import { SchedulesAPI } from '../../../api';
import buildRuleObj from '../shared/buildRuleObj';
import ScheduleForm from '../shared/ScheduleForm';

function ScheduleEdit({ i18n, schedule }) {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();
  const location = useLocation();
  const { pathname } = location;
  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  const handleSubmit = async values => {
    try {
      const rule = new RRule(buildRuleObj(values, i18n));
      const {
        data: { id: scheduleId },
      } = await SchedulesAPI.update(schedule.id, {
        name: values.name,
        description: values.description,
        rrule: rule.toString().replace(/\n/g, ' '),
      });

      history.push(`${pathRoot}schedules/${scheduleId}/details`);
    } catch (err) {
      setFormSubmitError(err);
    }
  };

  return (
    <Card>
      <CardBody>
        <ScheduleForm
          schedule={schedule}
          handleCancel={() =>
            history.push(`${pathRoot}schedules/${schedule.id}/details`)
          }
          handleSubmit={handleSubmit}
          submitError={formSubmitError}
        />
      </CardBody>
    </Card>
  );
}

ScheduleEdit.propTypes = {
  schedule: shape({}).isRequired,
};

ScheduleEdit.defaultProps = {};

export default withI18n()(ScheduleEdit);
