import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';
import { CardBody } from 'components/Card';
import { ProjectsAPI } from 'api';
import ProjectForm from '../shared/ProjectForm';

function ProjectAdd() {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();

  const handleSubmit = async (values) => {
    if (values.scm_type === 'manual') {
      values.scm_type = '';
    }
    if (!values.credential) {
      // Depending on the permissions of the user submitting the form,
      // the API might throw an unexpected error if our creation request
      // has a zero-length string as its credential field. As a work-around,
      // normalize falsey credential fields by deleting them.
      values.credential = null;
    } else if (typeof values.credential.id === 'number') {
      values.credential = values.credential.id;
    }
    if (values.scm_type === 'git') {
      if (!values.signature_validation_credential) {
        values.signature_validation_credential = null;
      } else if (
        typeof values.signature_validation_credential.id === 'number'
      ) {
        values.signature_validation_credential =
          values.signature_validation_credential.id;
      }
    }
    setFormSubmitError(null);
    try {
      const {
        data: { id },
      } = await ProjectsAPI.create({
        ...values,
        organization: values.organization.id,
        default_environment: values.default_environment?.id,
      });
      history.push(`/projects/${id}/details`);
    } catch (error) {
      setFormSubmitError(error);
    }
  };

  const handleCancel = () => {
    history.push(`/projects`);
  };

  return (
    <PageSection>
      <Card>
        <CardBody>
          <ProjectForm
            handleCancel={handleCancel}
            handleSubmit={handleSubmit}
            submitError={formSubmitError}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export default ProjectAdd;
