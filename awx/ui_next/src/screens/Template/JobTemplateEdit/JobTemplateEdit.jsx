/* eslint react/no-unused-state: 0 */
import React, { useState } from 'react';
import { withRouter, Redirect, useHistory } from 'react-router-dom';
import { CardBody } from '../../../components/Card';

import { JobTemplatesAPI } from '../../../api';
import { JobTemplate } from '../../../types';
import { getAddedAndRemoved } from '../../../util/lists';
import JobTemplateForm from '../shared/JobTemplateForm';

import ContentLoading from '../../../components/ContentLoading';

function JobTemplateEdit({ template }) {
  const history = useHistory();
  const [formSubmitError, setFormSubmitError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const detailsUrl = `/templates/${template.type}/${template.id}/details`;

  const handleSubmit = async values => {
    const {
      labels,
      instanceGroups,
      initialInstanceGroups,
      credentials,
      webhook_credential,
      webhook_key,
      webhook_url,
      ...remainingValues
    } = values;

    setFormSubmitError(null);
    setIsLoading(true);
    remainingValues.project = values.project.id;
    remainingValues.webhook_credential = webhook_credential?.id || null;
    try {
      await JobTemplatesAPI.update(template.id, remainingValues);
      await Promise.all([
        submitLabels(labels, template?.organization),
        submitInstanceGroups(instanceGroups, initialInstanceGroups),
        submitCredentials(credentials),
      ]);
      history.push(detailsUrl);
    } catch (error) {
      setFormSubmitError(error);
    } finally {
      setIsLoading(false);
    }
  };

  const submitLabels = async (labels = [], orgId) => {
    const { added, removed } = getAddedAndRemoved(
      template.summary_fields.labels.results,
      labels
    );

    const disassociationPromises = removed.map(label =>
      JobTemplatesAPI.disassociateLabel(template.id, label)
    );
    const associationPromises = added.map(label => {
      return JobTemplatesAPI.associateLabel(template.id, label, orgId);
    });

    const results = await Promise.all([
      ...disassociationPromises,
      ...associationPromises,
    ]);
    return results;
  };

  const submitInstanceGroups = async (groups, initialGroups) => {
    const { added, removed } = getAddedAndRemoved(initialGroups, groups);
    const disassociatePromises = await removed.map(group =>
      JobTemplatesAPI.disassociateInstanceGroup(template.id, group.id)
    );
    const associatePromises = await added.map(group =>
      JobTemplatesAPI.associateInstanceGroup(template.id, group.id)
    );
    return Promise.all([...disassociatePromises, ...associatePromises]);
  };

  const submitCredentials = async newCredentials => {
    const { added, removed } = getAddedAndRemoved(
      template.summary_fields.credentials,
      newCredentials
    );
    const disassociateCredentials = removed.map(cred =>
      JobTemplatesAPI.disassociateCredentials(template.id, cred.id)
    );
    const disassociatePromise = await Promise.all(disassociateCredentials);
    const associateCredentials = added.map(cred =>
      JobTemplatesAPI.associateCredentials(template.id, cred.id)
    );
    const associatePromise = Promise.all(associateCredentials);
    return Promise.all([disassociatePromise, associatePromise]);
  };

  const handleCancel = () => {
    history.push(detailsUrl);
  };

  const canEdit = template?.summary_fields?.user_capabilities?.edit;

  if (!canEdit) {
    return <Redirect to={detailsUrl} />;
  }
  if (isLoading) {
    return <ContentLoading />;
  }
  return (
    <CardBody>
      <JobTemplateForm
        template={template}
        handleCancel={handleCancel}
        handleSubmit={handleSubmit}
        submitError={formSubmitError}
      />
    </CardBody>
  );
}

JobTemplateEdit.propTypes = {
  template: JobTemplate.isRequired,
};

export default withRouter(JobTemplateEdit);
