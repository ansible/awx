import React, { useState } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Card,
  CardBody,
  CardHeader,
  PageSection,
  Tooltip,
} from '@patternfly/react-core';
import CardCloseButton from '@components/CardCloseButton';
import JobTemplateForm from '../shared/JobTemplateForm';
import { JobTemplatesAPI } from '@api';

function JobTemplateAdd({ history, i18n }) {
  const [error, setError] = useState('');

  const handleSubmit = async values => {
    try {
      const data = await JobTemplatesAPI.create(values);
      const { response } = data;
      history.push(`/templates/${response.type}/${response.id}/details`);
    } catch (err) {
      setError(err);
    }
  };

  const handleCancel = () => {
    history.push(`/templates`);
  };

  return (
    <PageSection>
      <Card>
        <CardHeader className="at-u-textRight">
          <Tooltip content={i18n._(t`Close`)} position="top">
            <CardCloseButton onClick={handleCancel} />
          </Tooltip>
        </CardHeader>
        <CardBody>
          <JobTemplateForm
            handleCancel={handleCancel}
            handleSubmit={handleSubmit}
          />
        </CardBody>
        {error ? <div>error</div> : ''}
      </Card>
    </PageSection>
  );
}

export default withI18n()(withRouter(JobTemplateAdd));
