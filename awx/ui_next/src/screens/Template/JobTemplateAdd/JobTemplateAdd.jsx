import React, { useState } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Card,
  CardBody,
  CardHeader,
  PageSection,
  Tooltip,
} from '@patternfly/react-core';
import CardCloseButton from '@components/CardCloseButton';
import JobTemplateForm from '../shared/JobTemplateForm';
import { JobTemplatesAPI } from '@api';

function JobTemplateAdd({ history, i18n }) {
  const [formSubmitError, setFormSubmitError] = useState(null);

  async function handleSubmit(values) {
    const {
      labels,
      organizationId,
      instanceGroups,
      initialInstanceGroups,
      credentials,
      ...remainingValues
    } = values;

    setFormSubmitError(null);
    try {
      const {
        data: { id, type },
      } = await JobTemplatesAPI.create(remainingValues);
      await Promise.all([
        submitLabels(id, labels, organizationId),
        submitInstanceGroups(id, instanceGroups),
        submitCredentials(id, credentials),
      ]);
      history.push(`/templates/${type}/${id}/details`);
    } catch (error) {
      setFormSubmitError(error);
    }
  }

  function submitLabels(templateId, labels = [], organizationId) {
    const associationPromises = labels
      .filter(label => !label.isNew)
      .map(label => JobTemplatesAPI.associateLabel(templateId, label));
    const creationPromises = labels
      .filter(label => label.isNew)
      .map(label =>
        JobTemplatesAPI.generateLabel(templateId, label, organizationId)
      );

    return Promise.all([...associationPromises, ...creationPromises]);
  }

  function submitInstanceGroups(templateId, addedGroups = []) {
    const associatePromises = addedGroups.map(group =>
      JobTemplatesAPI.associateInstanceGroup(templateId, group.id)
    );
    return Promise.all(associatePromises);
  }

  function submitCredentials(templateId, credentials = []) {
    const associateCredentials = credentials.map(cred =>
      JobTemplatesAPI.associateCredentials(templateId, cred.id)
    );
    return Promise.all(associateCredentials);
  }

  function handleCancel() {
    history.push(`/templates`);
  }

  return (
    <PageSection>
      <Card>
        <CardHeader className="at-u-textRight">
          <Tooltip content={i18n._(t`Close`)} position="top">
            <CardCloseButton onClick={handleCancel} />
          </Tooltip>
        </CardHeader>
        <CardBody>
          <JobTemplateForm
            handleCancel={handleCancel}
            handleSubmit={handleSubmit}
          />
        </CardBody>
        {formSubmitError ? <div>formSubmitError</div> : ''}
      </Card>
    </PageSection>
  );
}

export default withI18n()(withRouter(JobTemplateAdd));
