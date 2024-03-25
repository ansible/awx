import React, { useState } from 'react';
import { useHistory, useLocation } from 'react-router-dom';
import { shape } from 'prop-types';
import { Card } from '@patternfly/react-core';
import yaml from 'js-yaml';
import { OrganizationsAPI, SchedulesAPI } from 'api';
import { getAddedAndRemoved } from 'util/lists';
import { parseVariableField } from 'util/yaml';
import mergeExtraVars from 'util/prompt/mergeExtraVars';
import getSurveyValues from 'util/prompt/getSurveyValues';
import createNewLabels from 'util/labels';
import ScheduleForm from '../shared/ScheduleForm';
import buildRuleSet from '../shared/buildRuleSet';
import { CardBody } from '../../Card';

function generateExtraData(extra_vars, surveyValues, surveyConfiguration) {
  const extraVars = parseVariableField(
    yaml.dump(mergeExtraVars(extra_vars, surveyValues))
  );
  surveyConfiguration.spec.forEach((q) => {
    if (!surveyValues[q.variable]) {
      delete extraVars[q.variable];
    }
  });
  return extraVars;
}

function ScheduleEdit({
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
  const pathRoot = pathname.substring(0, pathname.indexOf('schedules'));

  const handleSubmit = async (
    values,
    launchConfiguration,
    surveyConfiguration,
    originalInstanceGroups,
    originalLabels,
    scheduleCredentials = [],
    isPromptTouched = false
  ) => {
    const {
      execution_environment,
      extra_vars = null,
      instance_groups,
      inventory,
      credentials = [],
      frequency,
      frequencyOptions,
      exceptionFrequency,
      exceptionOptions,
      timezone,
      labels,
      ...submitValues
    } = values;

    const surveyValues = getSurveyValues(values);

    if (
      isPromptTouched &&
      surveyConfiguration?.spec &&
      launchConfiguration?.ask_variables_on_launch
    ) {
      submitValues.extra_data = generateExtraData(
        extra_vars,
        surveyValues,
        surveyConfiguration
      );
    } else if (
      isPromptTouched &&
      surveyConfiguration?.spec &&
      !launchConfiguration?.ask_variables_on_launch
    ) {
      submitValues.extra_data = generateExtraData(
        schedule.extra_data,
        surveyValues,
        surveyConfiguration
      );
    } else if (
      isPromptTouched &&
      launchConfiguration?.ask_variables_on_launch
    ) {
      submitValues.extra_data = parseVariableField(extra_vars);
    }

    if (
      isPromptTouched &&
      launchConfiguration?.ask_inventory_on_launch &&
      inventory
    ) {
      submitValues.inventory = inventory.id;
    }

    if (
      isPromptTouched &&
      launchConfiguration?.ask_execution_environment_on_launch &&
      execution_environment
    ) {
      submitValues.execution_environment = execution_environment.id;
    }

    try {
      if (isPromptTouched && launchConfiguration?.ask_labels_on_launch) {
        const { labelIds, error } = createNewLabels(
          values.labels,
          resource.organization
        );

        if (error) {
          setFormSubmitError(error);
        } else {
          submitValues.labels = labelIds;
        }
      }

      const ruleSet = buildRuleSet(values);
      const requestData = {
        ...submitValues,
        rrule: ruleSet.toString().replace(/\n/g, ' '),
      };
      delete requestData.startDate;
      delete requestData.startTime;

      if (Object.keys(values).includes('daysToKeep')) {
        if (!requestData.extra_data) {
          requestData.extra_data = JSON.stringify({
            days: values.daysToKeep,
          });
        } else {
          if (typeof requestData.extra_data === 'string') {
            requestData.extra_data = JSON.parse(requestData.extra_data);
          }
          requestData.extra_data.days = values.daysToKeep;
        }
      }

      const cleanedRequestData = Object.keys(requestData)
        .filter((key) => !key.startsWith('survey_'))
        .reduce((acc, key) => {
          acc[key] = requestData[key];
          return acc;
        }, {});

      const {
        data: { id: scheduleId },
      } = await SchedulesAPI.update(schedule.id, cleanedRequestData);

      const { added: addedCredentials, removed: removedCredentials } =
        getAddedAndRemoved(
          [
            ...(resource?.summary_fields.credentials || []),
            ...scheduleCredentials,
          ],
          credentials
        );

      const { added: addedLabels, removed: removedLabels } = getAddedAndRemoved(
        originalLabels,
        labels
      );

      let organizationId = resource.organization;

      if (addedLabels.length > 0) {
        if (!organizationId) {
          const {
            data: { results },
          } = await OrganizationsAPI.read();
          organizationId = results[0].id;
        }
      }

      await Promise.all([
        ...removedCredentials.map(({ id }) =>
          SchedulesAPI.disassociateCredential(scheduleId, id)
        ),
        ...addedCredentials.map(({ id }) =>
          SchedulesAPI.associateCredential(scheduleId, id)
        ),
        ...removedLabels.map((label) =>
          SchedulesAPI.disassociateLabel(scheduleId, label)
        ),
        ...addedLabels.map((label) =>
          SchedulesAPI.associateLabel(scheduleId, label, organizationId)
        ),
        SchedulesAPI.orderInstanceGroups(
          scheduleId,
          instance_groups || [],
          originalInstanceGroups
        ),
      ]);

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

export default ScheduleEdit;
