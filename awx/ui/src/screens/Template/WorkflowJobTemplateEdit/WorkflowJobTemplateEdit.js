import React, { useState, useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';

import { CardBody } from 'components/Card';
import { getAddedAndRemoved } from 'util/lists';
import { WorkflowJobTemplatesAPI, OrganizationsAPI, UsersAPI } from 'api';
import { useConfig } from 'contexts/Config';
import useRequest from 'hooks/useRequest';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { WorkflowJobTemplateForm } from '../shared';

function WorkflowJobTemplateEdit({ template }) {
  const { me = {} } = useConfig();
  const history = useHistory();
  const [formSubmitError, setFormSubmitError] = useState(null);

  const handleSubmit = async (values) => {
    const {
      labels,
      inventory,
      organization,
      webhook_credential,
      webhook_key,
      limit,
      ...templatePayload
    } = values;
    templatePayload.inventory = inventory?.id || null;
    templatePayload.organization = organization?.id || null;
    templatePayload.webhook_credential = webhook_credential?.id || null;
    templatePayload.limit = limit === '' ? null : limit;

    const formOrgId =
      organization?.id || inventory?.summary_fields?.organization.id || null;
    try {
      await Promise.all(
        await submitLabels(formOrgId, template.organization, labels)
      );
      await WorkflowJobTemplatesAPI.update(template.id, templatePayload);
      history.push(`/templates/workflow_job_template/${template.id}/details`);
    } catch (err) {
      setFormSubmitError(err);
    }
  };

  const submitLabels = async (formOrgId, templateOrgId, labels = []) => {
    const { added, removed } = getAddedAndRemoved(
      template.summary_fields.labels.results,
      labels
    );
    let orgId = formOrgId || templateOrgId;
    if (!orgId) {
      // eslint-disable-next-line no-useless-catch
      try {
        const {
          data: { results },
        } = await OrganizationsAPI.read();
        orgId = results[0].id;
      } catch (err) {
        throw err;
      }
    }

    const disassociationPromises = await removed.map((label) =>
      WorkflowJobTemplatesAPI.disassociateLabel(template.id, label)
    );
    const associationPromises = await added.map((label) =>
      WorkflowJobTemplatesAPI.associateLabel(template.id, label, orgId)
    );
    const results = [...disassociationPromises, ...associationPromises];
    return results;
  };

  const handleCancel = () => {
    history.push(`/templates/workflow_job_template/${template.id}/details`);
  };

  const {
    isLoading,
    request: fetchUserRole,
    result: { orgAdminResults, isOrgAdmin },
    error: contentError,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { results, count },
      } = await UsersAPI.readAdminOfOrganizations(me?.id);
      return { isOrgAdmin: count > 0, orgAdminResults: results };
    }, [me.id]),
    { isOrgAdmin: false, orgAdminResults: null }
  );

  useEffect(() => {
    fetchUserRole();
  }, [fetchUserRole]);

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  if (isLoading || !orgAdminResults) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <WorkflowJobTemplateForm
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
        template={template}
        submitError={formSubmitError}
        isOrgAdmin={isOrgAdmin}
      />
    </CardBody>
  );
}
export default WorkflowJobTemplateEdit;
