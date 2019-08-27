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
  const [formSubmitError, setFormSubmitError] = useState(null);

  async function handleSubmit(values) {
    const { newLabels, removedLabels } = values;
    delete values.newLabels;
    delete values.removedLabels;

    setFormSubmitError(null);
    try {
      const {
        data: { id, type },
      } = await JobTemplatesAPI.create(values);
      await Promise.all([submitLabels(id, newLabels, removedLabels)]);
      history.push(`/templates/${type}/${id}/details`);
    } catch (error) {
      setFormSubmitError(error);
    }
  }

  async function submitLabels(id, newLabels = [], removedLabels = []) {
    const disassociationPromises = removedLabels.map(label =>
      JobTemplatesAPI.disassociateLabel(id, label)
    );
    const associationPromises = newLabels
      .filter(label => !label.organization)
      .map(label => JobTemplatesAPI.associateLabel(id, label));
    const creationPromises = newLabels
      .filter(label => label.organization)
      .map(label => JobTemplatesAPI.generateLabel(id, label));

    const results = await Promise.all([
      ...disassociationPromises,
      ...associationPromises,
      ...creationPromises,
    ]);
    return results;
  }

  function handleCancel() {
    history.push(`/templates`);
  }

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
        {formSubmitError ? <div>formSubmitError</div> : ''}
      </Card>
    </PageSection>
  );
}

export default withI18n()(withRouter(JobTemplateAdd));
