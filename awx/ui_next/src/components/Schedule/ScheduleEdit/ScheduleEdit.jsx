import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { useHistory, useLocation } from 'react-router-dom';
import { RRule } from 'rrule';
import { shape } from 'prop-types';
import { Card } from '@patternfly/react-core';
import yaml from 'js-yaml';
import { CardBody } from '../../Card';
import { SchedulesAPI } from '../../../api';
import buildRuleObj from '../shared/buildRuleObj';
import ScheduleForm from '../shared/ScheduleForm';
import { getAddedAndRemoved } from '../../../util/lists';

import { parseVariableField } from '../../../util/yaml';
import mergeExtraVars from '../../../util/prompt/mergeExtraVars';
import getSurveyValues from '../../../util/prompt/getSurveyValues';

function ScheduleEdit({ i18n, schedule, resource }) {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();
  const location = useLocation();
  const { pathname } = location;
  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  const handleSubmit = async (
    values,
    launchConfig,
    surveyConfig,
    scheduleCredentials = []
  ) => {
    const {
      inventory,
      credentials = [],
      end,
      frequency,
      interval,
      startDateTime,
      timezone,
      occurrences,
      runOn,
      runOnTheDay,
      runOnTheMonth,
      runOnDayMonth,
      runOnDayNumber,
      endDateTime,
      runOnTheOccurrence,
      daysOfWeek,
      ...submitValues
    } = values;
    const { added, removed } = getAddedAndRemoved(
      [...resource?.summary_fields.credentials, ...scheduleCredentials],
      credentials
    );

    let extraVars;
    const surveyValues = getSurveyValues(values);
    const initialExtraVars =
      launchConfig?.ask_variables_on_launch && (values.extra_vars || '---');
    if (surveyConfig?.spec) {
      extraVars = yaml.safeDump(mergeExtraVars(initialExtraVars, surveyValues));
    } else {
      extraVars = yaml.safeDump(mergeExtraVars(initialExtraVars, {}));
    }
    submitValues.extra_data = extraVars && parseVariableField(extraVars);
    delete values.extra_vars;
    if (inventory) {
      submitValues.inventory = inventory.id;
    }

    try {
      const rule = new RRule(buildRuleObj(values, i18n));
      const {
        data: { id: scheduleId },
      } = await SchedulesAPI.update(schedule.id, {
        ...submitValues,
        rrule: rule.toString().replace(/\n/g, ' '),
      });
      if (values.credentials?.length > 0) {
        await Promise.all([
          ...removed.map(({ id }) =>
            SchedulesAPI.disassociateCredential(scheduleId, id)
          ),
          ...added.map(({ id }) =>
            SchedulesAPI.associateCredential(scheduleId, id)
          ),
        ]);
      }

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
          resource={resource}
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
