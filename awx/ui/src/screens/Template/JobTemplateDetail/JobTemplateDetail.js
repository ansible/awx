import React, { useCallback, useEffect } from 'react';
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

import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import ChipGroup from 'components/ChipGroup';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import CredentialChip from 'components/CredentialChip';
import {
  Detail,
  DetailList,
  DeletedDetail,
  UserDateDetail,
} from 'components/DetailList';
import DeleteButton from 'components/DeleteButton';
import ErrorDetail from 'components/ErrorDetail';
import { LaunchButton } from 'components/LaunchButton';
import { VariablesDetail } from 'components/CodeEditor';
import { JobTemplatesAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import ExecutionEnvironmentDetail from 'components/ExecutionEnvironmentDetail';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import jtHelpTextStrings from '../shared/JobTemplate.helptext';

const helpText = jtHelpTextStrings();
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

  const deleteDetailsRequests =
    relatedResourceDeleteRequests.template(template);
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
    (option) => option.verbosity === verbosity
  );
  const generateCallBackUrl = `${window.location.origin + url}callback/`;
  const renderOptionsField =
    become_enabled ||
    host_config_key ||
    allow_simultaneous ||
    use_fact_cache ||
    webhook_service;

  const renderOptions = (
    <TextList component={TextListVariants.ul}>
      {become_enabled && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Privilege Escalation`}
        </TextListItem>
      )}
      {host_config_key && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Provisioning Callbacks`}
        </TextListItem>
      )}
      {allow_simultaneous && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Concurrent Jobs`}
        </TextListItem>
      )}
      {use_fact_cache && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Fact Storage`}
        </TextListItem>
      )}
      {webhook_service && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Webhooks`}
        </TextListItem>
      )}
    </TextList>
  );

  const inventoryValue = (kind, id) => {
    const inventorykind = kind === 'smart' ? 'smart_inventory' : 'inventory';

    return ask_inventory_on_launch ? (
      <>
        <Link to={`/inventories/${inventorykind}/${id}/details`}>
          {summary_fields.inventory.name}
        </Link>
        <span> {t`(Prompt on launch)`}</span>
      </>
    ) : (
      <Link to={`/inventories/${inventorykind}/${id}/details`}>
        {summary_fields.inventory.name}
      </Link>
    );
  };

  const buildLinkURL = (instance) =>
    instance.is_container_group
      ? '/instance_groups/container_group/'
      : '/instance_groups/';

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
        <Detail
          label={t`Description`}
          value={description}
          dataCy="jt-detail-description"
        />
        <Detail
          label={t`Job Type`}
          value={job_type}
          dataCy="jt-detail-job-type"
          helpText={helpText.jobType}
        />
        {summary_fields.organization ? (
          <Detail
            label={t`Organization`}
            dataCy="jt-detail-organization"
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
            dataCy="jt-detail-inventory"
            value={inventoryValue(
              summary_fields.inventory.kind,
              summary_fields.inventory.id
            )}
            helpText={helpText.inventory}
          />
        ) : (
          !ask_inventory_on_launch && (
            <DeletedDetail label={t`Inventory`} dataCy="jt-detail-inventory" />
          )
        )}
        {summary_fields.project ? (
          <Detail
            label={t`Project`}
            dataCy="jt-detail-project"
            value={
              <Link to={`/projects/${summary_fields.project.id}/details`}>
                {summary_fields.project.name}
              </Link>
            }
            helpText={helpText.project}
          />
        ) : (
          <DeletedDetail label={t`Project`} />
        )}
        <ExecutionEnvironmentDetail
          virtualEnvironment={custom_virtualenv}
          executionEnvironment={summary_fields?.resolved_environment}
          helpText={helpText.executionEnvironment}
          dataCy="jt-detail-execution-environment"
        />
        <Detail
          label={t`Source Control Branch`}
          value={template.scm_branch}
          dataCy="jt-detail-scm-branch"
        />
        <Detail
          label={t`Playbook`}
          value={playbook}
          dataCy="jt-detail-playbook"
          helpText={helpText.playbook}
        />
        <Detail
          label={t`Forks`}
          value={forks || '0'}
          dataCy="jt-detail-forks"
          helpText={helpText.forks}
        />
        <Detail
          label={t`Limit`}
          value={limit}
          dataCy="jt-detail-limit"
          helpText={helpText.limit}
        />
        <Detail
          label={t`Verbosity`}
          value={verbosityDetails[0].details}
          dataCy="jt-detail-verbosity"
          helpText={helpText.verbosity}
        />
        <Detail
          label={t`Timeout`}
          value={timeout || '0'}
          dataCy="jt-detail-timeout"
          helpText={helpText.timeout}
        />
        <Detail
          label={t`Show Changes`}
          value={diff_mode ? t`On` : t`Off`}
          dataCy="jt-detail-show-changes"
          helpText={helpText.showChanges}
        />
        <Detail
          label={t`Job Slicing`}
          value={job_slice_count}
          dataCy="jt-detail-job-slice-count"
          helpText={helpText.jobSlicing}
        />
        {host_config_key && (
          <>
            <Detail
              label={t`Host Config Key`}
              value={host_config_key}
              dataCy="jt-detail-host-config-key"
            />
            <Detail
              label={t`Provisioning Callback URL`}
              value={generateCallBackUrl}
              dataCy="jt-detail-provisioning-callback-url"
              helpText={helpText.provisioningCallbacks}
            />
          </>
        )}
        {webhook_service && (
          <Detail
            label={t`Webhook Service`}
            value={webhook_service === 'github' ? t`GitHub` : t`GitLab`}
            dataCy="jt-detail-webhook-service"
            helpText={helpText.webhookService}
          />
        )}
        {webhook_receiver && (
          <Detail
            label={t`Webhook URL`}
            value={`${document.location.origin}${webhook_receiver}`}
            dataCy="jt-detail-webhook-url"
            helpText={helpText.webhookURL}
          />
        )}
        <Detail
          label={t`Webhook Key`}
          value={webhook_key}
          dataCy="jt-detail-webhook-key"
          helpText={helpText.webhookKey}
        />
        {summary_fields.webhook_credential && (
          <Detail
            label={t`Webhook Credential`}
            dataCy="jt-detail-webhook-credential"
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
          label={t`Last Modified`}
          date={modified}
          user={summary_fields.modified_by}
        />
        {renderOptionsField && (
          <Detail
            fullWidth
            label={t`Enabled Options`}
            value={renderOptions}
            dataCy="jt-detail-enabled-options"
            helpText={helpText.enabledOptions}
          />
        )}
        {summary_fields.credentials && summary_fields.credentials.length > 0 && (
          <Detail
            fullWidth
            label={t`Credentials`}
            dataCy="jt-detail-credentials"
            helpText={helpText.credentials}
            value={
              <ChipGroup
                numChips={5}
                totalChips={summary_fields.credentials.length}
                ouiaId="jt-detail-credential-chips"
              >
                {summary_fields.credentials.map((c) => (
                  <Link to={`/credentials/${c.id}/details`} key={c.id}>
                    <CredentialChip
                      key={c.id}
                      credential={c}
                      ouiaId={`credential-${c.id}-chip`}
                      isReadOnly
                    />
                  </Link>
                ))}
              </ChipGroup>
            }
          />
        )}
        {summary_fields.labels && summary_fields.labels.results.length > 0 && (
          <Detail
            fullWidth
            label={t`Labels`}
            dataCy="jt-detail-labels"
            helpText={helpText.labels}
            value={
              <ChipGroup
                numChips={5}
                totalChips={summary_fields.labels.results.length}
                ouiaId="label-chips"
              >
                {summary_fields.labels.results.map((l) => (
                  <Chip key={l.id} ouiaId={`label-${l.id}-chip`} isReadOnly>
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
            dataCy="jt-detail-instance-groups"
            helpText={helpText.instanceGroups}
            value={
              <ChipGroup
                numChips={5}
                totalChips={instanceGroups.length}
                ouiaId="instance-group-chips"
              >
                {instanceGroups.map((ig) => (
                  <Link to={`${buildLinkURL(ig)}${ig.id}/details`} key={ig.id}>
                    <Chip
                      key={ig.id}
                      ouiaId={`instance-group-${ig.id}-chip`}
                      isReadOnly
                    >
                      {ig.name}
                    </Chip>
                  </Link>
                ))}
              </ChipGroup>
            }
          />
        )}
        {job_tags && job_tags.length > 0 && (
          <Detail
            fullWidth
            label={t`Job Tags`}
            dataCy="jt-detail-job-tags"
            helpText={helpText.jobTags}
            value={
              <ChipGroup
                numChips={5}
                totalChips={job_tags.split(',').length}
                ouiaId="job-tag-chips"
              >
                {job_tags.split(',').map((jobTag) => (
                  <Chip
                    key={jobTag}
                    ouiaId={`job-tag-${jobTag}-chip`}
                    isReadOnly
                  >
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
            dataCy="jt-detail-skip-tags"
            helpText={helpText.skipTags}
            value={
              <ChipGroup
                numChips={5}
                totalChips={skip_tags.split(',').length}
                ouiaId="skip-tag-chips"
              >
                {skip_tags.split(',').map((skipTag) => (
                  <Chip
                    key={skipTag}
                    ouiaId={`skip-tag-${skipTag}-chip`}
                    isReadOnly
                  >
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
          dataCy={`jt-detail-${template.id}`}
          name="extra_vars"
          helpText={helpText.variables}
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
            {({ handleLaunch, isLaunching }) => (
              <Button
                ouiaId="job-template-detail-launch-button"
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
              ouiaId="job-template-detail-delete-button"
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
