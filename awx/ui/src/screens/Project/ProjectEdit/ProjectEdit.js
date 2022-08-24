import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { Card } from '@patternfly/react-core';
import { CardBody } from 'components/Card';
import { ProjectsAPI } from 'api';
import ProjectForm from '../shared/ProjectForm';

function ProjectEdit({ project }) {
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
    if (!values.signature_validation_credential) {
      values.signature_validation_credential = null;
    } else if (typeof values.signature_validation_credential.id === 'number') {
      values.signature_validation_credential =
        values.signature_validation_credential.id;
    }

    try {
      const {
        data: { id },
      } = await ProjectsAPI.update(project.id, {
        ...values,
        organization: values.organization.id,
        default_environment: values.default_environment?.id || null,
      });
      history.push(`/projects/${id}/details`);
    } catch (error) {
      setFormSubmitError(error);
    }
  };

  const handleCancel = () => {
    history.push(`/projects/${project.id}/details`);
  };

  return (
    <Card>
      <CardBody>
        <ProjectForm
          project={project}
          handleCancel={handleCancel}
          handleSubmit={handleSubmit}
          submitError={formSubmitError}
        />
      </CardBody>
    </Card>
  );
}

export default ProjectEdit;
