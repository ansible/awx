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
    scheduleCredentials = [],
    originalLabels = []
  ) => {
    const {
      execution_environment,
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
    let extraVars;
    const surveyValues = getSurveyValues(values);

    if (
      !Object.values(surveyValues).length &&
      surveyConfiguration?.spec?.length
    ) {
      surveyConfiguration.spec.forEach((q) => {
        surveyValues[q.variable] = q.default;
      });
    }

    const initialExtraVars =
      launchConfiguration?.ask_variables_on_launch &&
      (values.extra_vars || '---');
    if (surveyConfiguration?.spec) {
      extraVars = yaml.dump(mergeExtraVars(initialExtraVars, surveyValues));
    } else {
      extraVars = yaml.dump(mergeExtraVars(initialExtraVars, {}));
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

    if (execution_environment) {
      submitValues.execution_environment = execution_environment.id;
    }

    try {
      if (launchConfiguration?.ask_labels_on_launch) {
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
          requestData.extra_data.days = values.daysToKeep;
        }
      }

      const {
        data: { id: scheduleId },
      } = await SchedulesAPI.update(schedule.id, requestData);

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
          instance_groups,
          resource?.summary_fields.instance_groups || []
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
