import React from 'react';
import { withRouter } from 'react-router-dom';
import TemplateList from '../../Template/TemplateList/TemplateList';

function ProjectJobTemplates() {
  return <TemplateList />;
}

export default withRouter(ProjectJobTemplates);
