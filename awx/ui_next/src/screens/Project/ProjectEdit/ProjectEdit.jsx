import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import styled from 'styled-components';
import { Card as _Card } from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import ProjectForm from '../shared/ProjectForm';
import { ProjectsAPI } from '@api';

// TODO: we are doing this in multiple add/edit screens -- move to
// common component?
const Card = styled(_Card)`
  --pf-c-card--child--PaddingLeft: 0;
  --pf-c-card--child--PaddingRight: 0;
`;

function ProjectEdit({ project }) {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();

  const handleSubmit = async values => {
    if (values.scm_type === 'manual') {
      values.scm_type = '';
    }
    try {
      const {
        data: { id },
      } = await ProjectsAPI.update(project.id, values);
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
        />
      </CardBody>
      {formSubmitError ? (
        <div className="formSubmitError">formSubmitError</div>
      ) : (
        ''
      )}
    </Card>
  );
}

export default ProjectEdit;
