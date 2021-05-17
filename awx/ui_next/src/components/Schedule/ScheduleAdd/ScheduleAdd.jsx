import React, { useState } from 'react';
import { func, shape } from 'prop-types';

import { useHistory, useLocation } from 'react-router-dom';
import { RRule } from 'rrule';
import { Card } from '@patternfly/react-core';
import yaml from 'js-yaml';
import { CardBody } from '../../Card';
import { parseVariableField } from '../../../util/yaml';

import buildRuleObj from '../shared/buildRuleObj';
import ScheduleForm from '../shared/ScheduleForm';
import { SchedulesAPI } from '../../../api';
import mergeExtraVars from '../../../util/prompt/mergeExtraVars';
import getSurveyValues from '../../../util/prompt/getSurveyValues';
import { getAddedAndRemoved } from '../../../util/lists';

function ScheduleAdd({
  resource,
  apiModel,
  launchConfig,
  surveyConfig,
  hasDaysToKeepField,
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
    surveyConfiguration
  ) => {
    const {
      inventory,
      extra_vars,
      originalCredentials,
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
      credentials,
      daysOfWeek,
      ...submitValues
    } = values;
    const { added } = getAddedAndRemoved(
      resource?.summary_fields.credentials,
      credentials
    );
    let extraVars;
    const surveyValues = getSurveyValues(values);

    if (
      !Object.values(surveyValues).length &&
      surveyConfiguration?.spec?.length
    ) {
      surveyConfiguration.spec.forEach(q => {
        surveyValues[q.variable] = q.default;
      });
    }
    const initialExtraVars =
      launchConfiguration?.ask_variables_on_launch &&
      (values.extra_vars || '---');
    if (surveyConfiguration?.spec) {
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
      const rule = new RRule(buildRuleObj(values));
      const requestData = {
        ...submitValues,
        rrule: rule.toString().replace(/\n/g, ' '),
      };

      if (Object.keys(values).includes('daysToKeep')) {
        if (requestData.extra_data) {
          requestData.extra_data.days = values.daysToKeep;
        } else {
          requestData.extra_data = JSON.stringify({
            days: values.daysToKeep,
          });
        }
      }

      const {
        data: { id: scheduleId },
      } = await apiModel.createSchedule(resource.id, requestData);
      if (credentials?.length > 0) {
        await Promise.all(
          added.map(({ id: credentialId }) =>
            SchedulesAPI.associateCredential(scheduleId, credentialId)
          )
        );
      }
      history.push(`${pathRoot}schedules/${scheduleId}`);
    } catch (err) {
      setFormSubmitError(err);
    }
  };

  return (
    <Card>
      <CardBody>
        <ScheduleForm
          hasDaysToKeepField={hasDaysToKeepField}
          handleCancel={() => history.push(`${pathRoot}schedules`)}
          handleSubmit={handleSubmit}
          submitError={formSubmitError}
          launchConfig={launchConfig}
          surveyConfig={surveyConfig}
          resource={resource}
          resourceDefaultCredentials={resourceDefaultCredentials}
        />
      </CardBody>
    </Card>
  );
}

ScheduleAdd.propTypes = {
  apiModel: shape({ createSchedule: func.isRequired }).isRequired,
};

ScheduleAdd.defaultProps = {};

export default ScheduleAdd;
