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

function ScheduleEdit({
  i18n,
  hasDaysToKeepField,
  schedule,
  resource,
  launchConfig,
  surveyConfig,
  resourceDefaultCredentials,
}) {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();
  const location = useLocation();
  const { pathname } = location;
  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  const handleSubmit = async (
    values,
    launchConfiguration,
    surveyConfiguration,
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
      occurences,
      runOn,
      runOnTheDay,
      runOnTheMonth,
      runOnDayMonth,
      runOnDayNumber,
      endDateTime,
      runOnTheOccurence,
      daysOfWeek,
      ...submitValues
    } = values;
    const { added, removed } = getAddedAndRemoved(
      [...(resource?.summary_fields.credentials || []), ...scheduleCredentials],
      credentials
    );

    let extraVars;
    const surveyValues = getSurveyValues(values);
    const initialExtraVars =
      launchConfiguration?.ask_variables_on_launch &&
      (values.extra_vars || '---');
    if (surveyConfiguration?.spec) {
      extraVars = yaml.safeDump(mergeExtraVars(initialExtraVars, surveyValues));
    } else {
      extraVars = yaml.safeDump(mergeExtraVars(initialExtraVars, {}));
    }
    submitValues.extra_data = extraVars && parseVariableField(extraVars);

    if (
      Object.keys(submitValues.extra_data).length === 0 &&
      Object.keys(schedule.extra_data).length > 0
    ) {
      submitValues.extra_data = schedule.extra_data;
    }
    delete values.extra_vars;
    if (inventory) {
      submitValues.inventory = inventory.id;
    }

    try {
      const rule = new RRule(buildRuleObj(values, i18n));
      const requestData = {
        ...submitValues,
        rrule: rule.toString().replace(/\n/g, ' '),
      };

      if (Object.keys(values).includes('daysToKeep')) {
        if (!requestData.extra_data) {
          requestData.extra_data = JSON.stringify({ days: values.daysToKeep });
        } else {
          requestData.extra_data.days = values.daysToKeep;
        }
      }

      const {
        data: { id: scheduleId },
      } = await SchedulesAPI.update(schedule.id, requestData);
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
          hasDaysToKeepField={hasDaysToKeepField}
          handleCancel={() =>
            history.push(`${pathRoot}schedules/${schedule.id}/details`)
          }
          handleSubmit={handleSubmit}
          submitError={formSubmitError}
          resource={resource}
          launchConfig={launchConfig}
          surveyConfig={surveyConfig}
          resourceDefaultCredentials={resourceDefaultCredentials}
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
