import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card } from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import ErrorDetail from '@components/ErrorDetail';
import AlertModal from '@components/AlertModal';
import JobTemplateForm from '../shared/JobTemplateForm';
import { JobTemplatesAPI } from '@api';

function JobTemplateAdd({ i18n }) {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();

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
      // check for field-specific errors from API
      if (error.response?.data && typeof error.response.data === 'object') {
        throw error.response.data;
      }
      setFormSubmitError(error);
    }
  }

  function submitLabels(templateId, labels = [], organizationId) {
    const associationPromises = labels.map(label =>
      JobTemplatesAPI.associateLabel(templateId, label, organizationId)
    );
    return Promise.all([...associationPromises]);
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
    <Card>
      <CardBody>
        <JobTemplateForm
          handleCancel={handleCancel}
          handleSubmit={handleSubmit}
        />
      </CardBody>
      {formSubmitError && (
        <AlertModal
          variant="danger"
          title={i18n._(t`Error!`)}
          isOpen={formSubmitError}
          onClose={() => setFormSubmitError(null)}
        >
          {i18n._(t`An error occurred when saving`)}
          <ErrorDetail error={formSubmitError} />
        </AlertModal>
      )}
    </Card>
  );
}

export default withI18n()(JobTemplateAdd);
