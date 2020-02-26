import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';

import { Card, PageSection } from '@patternfly/react-core';
import { CardBody } from '@components/Card';

import { WorkflowJobTemplatesAPI, OrganizationsAPI } from '@api';
import WorkflowJobTemplateForm from '../shared/WorkflowJobTemplateForm';

function WorkflowJobTemplateAdd() {
  const history = useHistory();
  const [formSubmitError, setFormSubmitError] = useState(null);

  const handleSubmit = async values => {
    const { labels, organizationId, ...remainingValues } = values;
    try {
      const {
        data: { id },
      } = await WorkflowJobTemplatesAPI.create(remainingValues);
      await Promise.all([submitLabels(id, labels, organizationId, values)]);
      history.push(`/templates/workflow_job_template/${id}/details`);
    } catch (err) {
      setFormSubmitError(err);
    }
  };

  const submitLabels = async (
    templateId,
    labels = [],
    organizationId,
    values
  ) => {
    if (!organizationId && !values.organization) {
      try {
        const {
          data: { results },
        } = await OrganizationsAPI.read();
        organizationId = results[0].id;
      } catch (err) {
        setFormSubmitError(err);
      }
    }
    const associatePromises = labels.map(label =>
      WorkflowJobTemplatesAPI.associateLabel(templateId, label, organizationId)
    );
    return Promise.all([...associatePromises]);
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
