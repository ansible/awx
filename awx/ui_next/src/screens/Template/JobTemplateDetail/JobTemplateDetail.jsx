import React, { Fragment, useCallback, useEffect } from 'react';
import { Link, useHistory, useParams } from 'react-router-dom';

import {
  Button,
  Chip,
  TextList,
  TextListItem,
  TextListItemVariants,
  TextListVariants,
  Label,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';

import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import ChipGroup from '../../../components/ChipGroup';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import CredentialChip from '../../../components/CredentialChip';
import {
  Detail,
  DetailList,
  DeletedDetail,
  UserDateDetail,
} from '../../../components/DetailList';
import DeleteButton from '../../../components/DeleteButton';
import ErrorDetail from '../../../components/ErrorDetail';
import { LaunchButton } from '../../../components/LaunchButton';
import { VariablesDetail } from '../../../components/CodeEditor';
import { JobTemplatesAPI } from '../../../api';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import ExecutionEnvironmentDetail from '../../../components/ExecutionEnvironmentDetail';
import { relatedResourceDeleteRequests } from '../../../util/getRelatedResourceDeleteDetails';

function JobTemplateDetail({ template }) {
  const {
    ask_inventory_on_launch,
    allow_simultaneous,
    become_enabled,
    created,
    description,
    diff_mode,
    extra_vars,
    forks,
    host_config_key,
    job_slice_count,
    job_tags,
    job_type,
    name,
    limit,
    modified,
    playbook,
    skip_tags,
    timeout,
    summary_fields,
    use_fact_cache,
    url,
    verbosity,
    webhook_service,
    related: { webhook_receiver },
    webhook_key,
    custom_virtualenv,
  } = template;
  const { id: templateId } = useParams();
  const history = useHistory();

  const {
    isLoading: isLoadingInstanceGroups,
    request: fetchInstanceGroups,
    error: instanceGroupsError,
    result: { instanceGroups },
  } = useRequest(
    useCallback(async () => {
      const {
        data: { results },
      } = await JobTemplatesAPI.readInstanceGroups(templateId);
      return { instanceGroups: results };
    }, [templateId]),
    { instanceGroups: [] }
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  const {
    request: deleteJobTemplate,
    isLoading: isDeleteLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await JobTemplatesAPI.destroy(templateId);
      history.push(`/templates`);
    }, [templateId, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);

  const deleteDetailsRequests = relatedResourceDeleteRequests.template(
    template
  );
  const canLaunch =
    summary_fields.user_capabilities && summary_fields.user_capabilities.start;
  const verbosityOptions = [
    { verbosity: 0, details: t`0 (Normal)` },
    { verbosity: 1, details: t`1 (Verbose)` },
    { verbosity: 2, details: t`2 (More Verbose)` },
    { verbosity: 3, details: t`3 (Debug)` },
    { verbosity: 4, details: t`4 (Connection Debug)` },
    { verbosity: 5, details: t`5 (WinRM Debug)` },
  ];
  const verbosityDetails = verbosityOptions.filter(
    option => option.verbosity === verbosity
  );
  const generateCallBackUrl = `${window.location.origin + url}callback/`;
  const renderOptionsField =
    become_enabled || host_config_key || allow_simultaneous || use_fact_cache;

  const renderOptions = (
    <TextList component={TextListVariants.ul}>
      {become_enabled && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Enable Privilege Escalation`}
        </TextListItem>
      )}
      {host_config_key && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Allow Provisioning Callbacks`}
        </TextListItem>
      )}
      {allow_simultaneous && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Enable Concurrent Jobs`}
        </TextListItem>
      )}
      {use_fact_cache && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Use Fact Storage`}
        </TextListItem>
      )}
    </TextList>
  );

  const inventoryValue = (kind, id) => {
    const inventorykind = kind === 'smart' ? 'smart_inventory' : 'inventory';

    return ask_inventory_on_launch ? (
      <Fragment>
        <Link to={`/inventories/${inventorykind}/${id}/details`}>
          {summary_fields.inventory.name}
        </Link>
        <span> {t`(Prompt on launch)`}</span>
      </Fragment>
    ) : (
      <Link to={`/inventories/${inventorykind}/${id}/details`}>
        {summary_fields.inventory.name}
      </Link>
    );
  };

  if (instanceGroupsError) {
    return <ContentError error={instanceGroupsError} />;
  }

  if (isLoadingInstanceGroups || isDeleteLoading) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail label={t`Name`} value={name} dataCy="jt-detail-name" />
        <Detail label={t`Description`} value={description} />
        <Detail label={t`Job Type`} value={job_type} />
        {summary_fields.organization ? (
          <Detail
            label={t`Organization`}
            value={
              <Link
                to={`/organizations/${summary_fields.organization.id}/details`}
              >
                {summary_fields.organization.name}
              </Link>
            }
          />
        ) : (
          <DeletedDetail label={t`Organization`} />
        )}
        {summary_fields.inventory ? (
          <Detail
            label={t`Inventory`}
            value={inventoryValue(
              summary_fields.inventory.kind,
              summary_fields.inventory.id
            )}
          />
        ) : (
          !ask_inventory_on_launch && <DeletedDetail label={t`Inventory`} />
        )}
        {summary_fields.project ? (
          <Detail
            label={t`Project`}
            value={
              <Link to={`/projects/${summary_fields.project.id}/details`}>
                {summary_fields.project.name}
              </Link>
            }
          />
        ) : (
          <DeletedDetail label={t`Project`} />
        )}
        <ExecutionEnvironmentDetail
          virtualEnvironment={custom_virtualenv}
          executionEnvironment={summary_fields?.execution_environment}
        />
        <Detail label={t`Source Control Branch`} value={template.scm_branch} />
        <Detail label={t`Playbook`} value={playbook} />
        <Detail label={t`Forks`} value={forks || '0'} />
        <Detail label={t`Limit`} value={limit} />
        <Detail label={t`Verbosity`} value={verbosityDetails[0].details} />
        <Detail label={t`Timeout`} value={timeout || '0'} />
        <Detail label={t`Show Changes`} value={diff_mode ? t`On` : t`Off`} />
        <Detail label={t`Job Slicing`} value={job_slice_count} />
        {host_config_key && (
          <React.Fragment>
            <Detail label={t`Host Config Key`} value={host_config_key} />
            <Detail
              label={t`Provisioning Callback URL`}
              value={generateCallBackUrl}
            />
          </React.Fragment>
        )}
        {webhook_service && (
          <Detail
            label={t`Webhook Service`}
            value={webhook_service === 'github' ? t`GitHub` : t`GitLab`}
          />
        )}
        {webhook_receiver && (
          <Detail
            label={t`Webhook URL`}
            value={`${document.location.origin}${webhook_receiver}`}
          />
        )}
        <Detail label={t`Webhook Key`} value={webhook_key} />
        {summary_fields.webhook_credential && (
          <Detail
            label={t`Webhook Credential`}
            value={
              <Link
                to={`/credentials/${summary_fields.webhook_credential.id}/details`}
              >
                <Label>{summary_fields.webhook_credential.name}</Label>
              </Link>
            }
          />
        )}
        {renderOptionsField && (
          <Detail label={t`Options`} value={renderOptions} />
        )}
        <UserDateDetail
          label={t`Created`}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={t`Last Modified`}
          date={modified}
          user={summary_fields.modified_by}
        />
        {summary_fields.credentials && summary_fields.credentials.length > 0 && (
          <Detail
            fullWidth
            label={t`Credentials`}
            value={
              <ChipGroup
                numChips={5}
                totalChips={summary_fields.credentials.length}
              >
                {summary_fields.credentials.map(c => (
                  <CredentialChip key={c.id} credential={c} isReadOnly />
                ))}
              </ChipGroup>
            }
          />
        )}
        {summary_fields.labels && summary_fields.labels.results.length > 0 && (
          <Detail
            fullWidth
            label={t`Labels`}
            value={
              <ChipGroup
                numChips={5}
                totalChips={summary_fields.labels.results.length}
              >
                {summary_fields.labels.results.map(l => (
                  <Chip key={l.id} isReadOnly>
                    {l.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {instanceGroups.length > 0 && (
          <Detail
            fullWidth
            label={t`Instance Groups`}
            value={
              <ChipGroup numChips={5} totalChips={instanceGroups.length}>
                {instanceGroups.map(ig => (
                  <Chip key={ig.id} isReadOnly>
                    {ig.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {job_tags && job_tags.length > 0 && (
          <Detail
            fullWidth
            label={t`Job Tags`}
            value={
              <ChipGroup numChips={5} totalChips={job_tags.split(',').length}>
                {job_tags.split(',').map(jobTag => (
                  <Chip key={jobTag} isReadOnly>
                    {jobTag}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {skip_tags && skip_tags.length > 0 && (
          <Detail
            fullWidth
            label={t`Skip Tags`}
            value={
              <ChipGroup numChips={5} totalChips={skip_tags.split(',').length}>
                {skip_tags.split(',').map(skipTag => (
                  <Chip key={skipTag} isReadOnly>
                    {skipTag}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        <VariablesDetail
          value={extra_vars}
          rows={4}
          label={t`Variables`}
          dataCy={`jt-details-${template.id}`}
        />
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              ouiaId="job-template-detail-edit-button"
              component={Link}
              to={`/templates/job_template/${templateId}/edit`}
              aria-label={t`Edit`}
            >
              {t`Edit`}
            </Button>
          )}
        {canLaunch && (
          <LaunchButton resource={template} aria-label={t`Launch`}>
            {({ handleLaunch }) => (
              <Button
                ouiaId="job-template-detail-launch-button"
                variant="secondary"
                type="submit"
                onClick={handleLaunch}
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
              modalTitle={t`Delete Job Template`}
              onConfirm={deleteJobTemplate}
              isDisabled={isDeleteLoading}
              deleteDetailsRequests={deleteDetailsRequests}
              deleteMessage={t`This job template is currently being used by other resources. Are you sure you want to delete it?`}
            >
              {t`Delete`}
            </DeleteButton>
          )}
      </CardActionsRow>
      {/* Update delete modal to show dependencies https://github.com/ansible/awx/issues/5546 */}
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to delete job template.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export { JobTemplateDetail as _JobTemplateDetail };
export default JobTemplateDetail;
