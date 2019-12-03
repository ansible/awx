import React, { useState } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import {
  Card as _Card,
  CardBody,
  CardHeader,
  Tooltip,
} from '@patternfly/react-core';
import CardCloseButton from '@components/CardCloseButton';
import ProjectForm from '../shared/ProjectForm';
import { ProjectsAPI } from '@api';

const Card = styled(_Card)`
  --pf-c-card--child--PaddingLeft: 0;
  --pf-c-card--child--PaddingRight: 0;
`;

function ProjectEdit({ project, history, i18n }) {
  const [formSubmitError, setFormSubmitError] = useState(null);

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
      <CardHeader css="text-align: right">
        <Tooltip content={i18n._(t`Close`)} position="top">
          <CardCloseButton onClick={handleCancel} />
        </Tooltip>
      </CardHeader>
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

export default withI18n()(withRouter(ProjectEdit));
