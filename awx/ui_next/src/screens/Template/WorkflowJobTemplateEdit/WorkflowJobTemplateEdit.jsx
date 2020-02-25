import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';

import { CardBody } from '@components/Card';
import { getAddedAndRemoved } from '@util/lists';
import { WorkflowJobTemplatesAPI, OrganizationsAPI } from '@api';
import { WorkflowJobTemplateForm } from '../shared';

function WorkflowJobTemplateEdit({ template, webhook_key }) {
  const history = useHistory();
  const [formSubmitError, setFormSubmitError] = useState();

  const handleSubmit = async values => {
    const { labels, ...remainingValues } = values;
    try {
      await WorkflowJobTemplatesAPI.update(template.id, remainingValues);
      await Promise.all([submitLabels(labels, values.organization)]);
      history.push(`/templates/workflow_job_template/${template.id}/details`);
    } catch (err) {
      setFormSubmitError(err);
    }
  };

  const submitLabels = async (labels = [], orgId) => {
    const { added, removed } = getAddedAndRemoved(
      template.summary_fields.labels.results,
      labels
    );
    if (!orgId && !template.organization) {
      try {
        const {
          data: { results },
        } = await OrganizationsAPI.read();
        orgId = results[0].id;
      } catch (err) {
        setFormSubmitError(err);
      }
    }

    const disassociationPromises = removed.map(label =>
      WorkflowJobTemplatesAPI.disassociateLabel(template.id, label)
    );

    const associationPromises = added.map(label => {
      return WorkflowJobTemplatesAPI.associateLabel(
        template.id,
        label,
        orgId || template.organization
      );
    });

    const results = await Promise.all([
      ...disassociationPromises,
      ...associationPromises,
    ]);
    return results;
  };

  const handleCancel = () => {
    history.push(`/templates`);
  };

  return (
    <>
      <CardBody>
        <WorkflowJobTemplateForm
          handleSubmit={handleSubmit}
          handleCancel={handleCancel}
          template={template}
          webhook_key={webhook_key}
          submitError={formSubmitError}
        />
      </CardBody>
    </>
  );
}
export default WorkflowJobTemplateEdit;
