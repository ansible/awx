import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import styled from 'styled-components';
import { Card as _Card, PageSection } from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import ProjectForm from '../shared/ProjectForm';
import { ProjectsAPI } from '@api';

const Card = styled(_Card)`
  --pf-c-card--child--PaddingLeft: 0;
  --pf-c-card--child--PaddingRight: 0;
`;

function ProjectAdd() {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();

  const handleSubmit = async values => {
    if (values.scm_type === 'manual') {
      values.scm_type = '';
    }
    setFormSubmitError(null);
    try {
      const {
        data: { id },
      } = await ProjectsAPI.create(values);
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
          />
        </CardBody>
        {formSubmitError ? (
          <div className="formSubmitError">formSubmitError</div>
        ) : (
          ''
        )}
      </Card>
    </PageSection>
  );
}

export default ProjectAdd;
