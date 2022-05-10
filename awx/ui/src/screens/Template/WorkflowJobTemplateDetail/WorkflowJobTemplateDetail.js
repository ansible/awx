import React, { useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';
import {
  Chip,
  Button,
  TextList,
  TextListItem,
  TextListVariants,
  TextListItemVariants,
  Label,
} from '@patternfly/react-core';
import { WorkflowJobTemplatesAPI } from 'api';

import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import ChipGroup from 'components/ChipGroup';
import { VariablesDetail } from 'components/CodeEditor';
import DeleteButton from 'components/DeleteButton';
import { DetailList, Detail, UserDateDetail } from 'components/DetailList';
import ErrorDetail from 'components/ErrorDetail';
import { LaunchButton } from 'components/LaunchButton';
import Sparkline from 'components/Sparkline';
import { toTitleCase } from 'util/strings';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import wfHelpTextStrings from '../shared/WorkflowJobTemplate.helptext';

const helpText = wfHelpTextStrings();

function WorkflowJobTemplateDetail({ template }) {
  const {
    id,
    ask_inventory_on_launch,
    name,
    description,
    type,
    extra_vars,
    created,
    modified,
    summary_fields,
    related,
    webhook_credential,
    webhook_key,
    scm_branch: scmBranch,
    limit,
  } = template;

  const urlOrigin = window.location.origin;
  const history = useHistory();

  const renderOptionsField =
    template.allow_simultaneous || template.webhook_service;

  const renderOptions = (
    <TextList component={TextListVariants.ul}>
      {template.allow_simultaneous && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Concurrent Jobs`}
        </TextListItem>
      )}
      {template.webhook_service && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Webhooks`}
        </TextListItem>
      )}
    </TextList>
  );

  const {
    request: deleteWorkflowJobTemplate,
    isLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await WorkflowJobTemplatesAPI.destroy(id);
      history.push(`/templates`);
    }, [id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);

  const inventoryValue = (kind, inventoryId) => {
    const inventorykind = kind === 'smart' ? 'smart_inventory' : 'inventory';

    return ask_inventory_on_launch ? (
      <>
        <Link to={`/inventories/${inventorykind}/${inventoryId}/details`}>
          <Label>{summary_fields.inventory.name}</Label>
        </Link>
        <span> {t`(Prompt on launch)`}</span>
      </>
    ) : (
      <Link to={`/inventories/${inventorykind}/${inventoryId}/details`}>
        <Label>{summary_fields.inventory.name}</Label>
      </Link>
    );
  };

  const canLaunch = summary_fields?.user_capabilities?.start;
  const recentPlaybookJobs = summary_fields.recent_jobs.map((job) => ({
    ...job,
    type: 'workflow_job',
  }));

  const deleteDetailsRequests =
    relatedResourceDeleteRequests.template(template);

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail label={t`Name`} value={name} dataCy="jt-detail-name" />
        <Detail label={t`Description`} value={description} />
        {summary_fields.recent_jobs?.length > 0 && (
          <Detail
            value={<Sparkline jobs={recentPlaybookJobs} />}
            label={t`Activity`}
          />
        )}
        {summary_fields.organization && (
          <Detail
            label={t`Organization`}
            value={
              <Link
                to={`/organizations/${summary_fields.organization.id}/details`}
              >
                <Label>{summary_fields.organization.name}</Label>
              </Link>
            }
          />
        )}
        {scmBranch && (
          <Detail
            dataCy="source-control-branch"
            label={t`Source Control Branch`}
            value={scmBranch}
            helpText={helpText.sourceControlBranch}
          />
        )}
        <Detail label={t`Job Type`} value={toTitleCase(type)} />
        {summary_fields.inventory && (
          <Detail
            label={t`Inventory`}
            helpText={helpText.inventory}
            value={inventoryValue(
              summary_fields.inventory.kind,
              summary_fields.inventory.id
            )}
          />
        )}
        <Detail
          dataCy="limit"
          label={t`Limit`}
          value={limit}
          helpText={helpText.limit}
        />
        <Detail
          label={t`Webhook Service`}
          value={toTitleCase(template.webhook_service)}
          helpText={helpText.webhookService}
        />
        {related.webhook_receiver && (
          <Detail
            label={t`Webhook URL`}
            helpText={helpText.webhookURL}
            value={`${urlOrigin}${template.related.webhook_receiver}`}
          />
        )}
        <Detail
          label={t`Webhook Key`}
          value={webhook_key}
          helpText={helpText.webhookKey}
        />
        {webhook_credential && (
          <Detail
            fullWidth
            label={t`Webhook Credentials`}
            helpText={helpText.webhookCredential}
            value={
              <Link
                to={`/credentials/${summary_fields.webhook_credential.id}/details`}
              >
                <Label>{summary_fields.webhook_credential.name}</Label>
              </Link>
            }
          />
        )}
        <UserDateDetail
          label={t`Created`}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={t`Modified`}
          date={modified}
          user={summary_fields.modified_by}
        />
        {renderOptionsField && (
          <Detail
            fullWidth
            label={t`Enabled Options`}
            value={renderOptions}
            helpText={helpText.enabledOptions}
          />
        )}
        {summary_fields.labels?.results?.length > 0 && (
          <Detail
            fullWidth
            label={t`Labels`}
            helpText={helpText.labels}
            value={
              <ChipGroup
                numChips={3}
                totalChips={summary_fields.labels.results.length}
                ouiaId="workflow-job-template-detail-label-chips"
              >
                {summary_fields.labels.results.map((l) => (
                  <Chip key={l.id} ouiaId={`${l.name}-label-chip`} isReadOnly>
                    {l.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        <VariablesDetail
          dataCy="workflow-job-template-detail-extra-vars"
          helpText={helpText.variables}
          label={t`Variables`}
          value={extra_vars}
          rows={4}
          name="extra_vars"
        />
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              ouiaId="workflow-job-template-detail-edit-button"
              component={Link}
              to={`/templates/workflow_job_template/${id}/edit`}
              aria-label={t`Edit`}
            >
              {t`Edit`}
            </Button>
          )}
        {canLaunch && (
          <LaunchButton resource={template} aria-label={t`Launch`}>
            {({ handleLaunch, isLaunching }) => (
              <Button
                ouiaId="workflow-job-template-detail-launch-button"
                variant="secondary"
                type="submit"
                onClick={handleLaunch}
                isDisabled={isLaunching}
              >
                {t`Launch`}
              </Button>
            )}
          </LaunchButton>
        )}
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={name}
              modalTitle={t`Delete Workflow Job Template`}
              onConfirm={deleteWorkflowJobTemplate}
              isDisabled={isLoading}
              deleteDetailsRequests={deleteDetailsRequests}
              deleteMessage={t`This workflow job template is currently being used by other resources. Are you sure you want to delete it?`}
            >
              {t`Delete`}
            </DeleteButton>
          )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to delete workflow job template.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}
export { WorkflowJobTemplateDetail as _WorkflowJobTemplateDetail };
export default WorkflowJobTemplateDetail;
