import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';
import { CardBody } from 'components/Card';
import { JobTemplatesAPI, OrganizationsAPI } from 'api';
import JobTemplateForm from '../shared/JobTemplateForm';

function JobTemplateAdd() {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();

  async function handleSubmit(values) {
    const {
      labels,
      instanceGroups,
      initialInstanceGroups,
      inventory,
      project,
      credentials,
      webhook_credential,
      webhook_key,
      webhook_url,
      ...remainingValues
    } = values;

    setFormSubmitError(null);
    remainingValues.project = project.id;
    remainingValues.webhook_credential = webhook_credential?.id;
    remainingValues.inventory = inventory?.id || null;
    try {
      const {
        data: { id, type },
      } = await JobTemplatesAPI.create({
        ...remainingValues,
        execution_environment: values.execution_environment?.id,
      });
      await Promise.all([
        submitLabels(id, labels, values.project.summary_fields.organization.id),
        submitInstanceGroups(id, instanceGroups),
        submitCredentials(id, credentials),
      ]);
      history.push(`/templates/${type}/${id}/details`);
    } catch (error) {
      setFormSubmitError(error);
    }
  }

  async function submitLabels(templateId, labels = [], orgId) {
    if (!orgId) {
      // eslint-disable-next-line no-useless-catch
      try {
        const {
          data: { results },
        } = await OrganizationsAPI.read();
        orgId = results[0].id;
      } catch (err) {
        throw err;
      }
    }
    const associationPromises = labels.map((label) =>
      JobTemplatesAPI.associateLabel(templateId, label, orgId)
    );

    return Promise.all([...associationPromises]);
  }

  async function submitInstanceGroups(templateId, addedGroups = []) {
    /* eslint-disable no-await-in-loop, no-restricted-syntax */
    // Resolve Promises sequentially to maintain order and avoid race condition
    for (const group of addedGroups) {
      await JobTemplatesAPI.associateInstanceGroup(templateId, group.id);
    }
    /* eslint-enable no-await-in-loop, no-restricted-syntax */
  }

  function submitCredentials(templateId, credentials = []) {
    const associateCredentials = credentials.map((cred) =>
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
        <CardBody>
          <JobTemplateForm
            handleCancel={handleCancel}
            handleSubmit={handleSubmit}
            submitError={formSubmitError}
            isOverrideDisabledLookup
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export default JobTemplateAdd;
