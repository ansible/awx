import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';

import { Card, PageSection } from '@patternfly/react-core';
import { CardBody } from '../../../components/Card';

import { WorkflowJobTemplatesAPI, OrganizationsAPI } from '../../../api';
import WorkflowJobTemplateForm from '../shared/WorkflowJobTemplateForm';

function WorkflowJobTemplateAdd() {
  const history = useHistory();
  const [formSubmitError, setFormSubmitError] = useState(null);

  const handleSubmit = async values => {
    const {
      labels,
      inventory,
      organization,
      webhook_credential,
      webhook_key,
      ...templatePayload
    } = values;
    templatePayload.inventory = inventory?.id;
    templatePayload.organization = organization?.id;
    templatePayload.webhook_credential = webhook_credential?.id;
    const organizationId =
      organization?.id || inventory?.summary_fields?.organization.id;
    try {
      const {
        data: { id },
      } = await WorkflowJobTemplatesAPI.create(templatePayload);
      await Promise.all(await submitLabels(id, labels, organizationId));
      history.push(`/templates/workflow_job_template/${id}/visualizer`);
    } catch (err) {
      setFormSubmitError(err);
    }
  };

  const submitLabels = async (templateId, labels = [], organizationId) => {
    if (!organizationId) {
      try {
        const {
          data: { results },
        } = await OrganizationsAPI.read();
        organizationId = results[0].id;
      } catch (err) {
        throw err;
      }
    }
    const associatePromises = labels.map(label =>
      WorkflowJobTemplatesAPI.associateLabel(templateId, label, organizationId)
    );
    return [...associatePromises];
  };

  const handleCancel = () => {
    history.push(`/templates`);
  };

  return (
    <PageSection>
      <Card>
        <CardBody>
          <WorkflowJobTemplateForm
            handleCancel={handleCancel}
            handleSubmit={handleSubmit}
            submitError={formSubmitError}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export default WorkflowJobTemplateAdd;
