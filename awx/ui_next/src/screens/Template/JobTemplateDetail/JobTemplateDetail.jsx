import React, { Fragment, useState, useEffect, useCallback } from 'react';
import { Link, useHistory, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
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
import LaunchButton from '../../../components/LaunchButton';
import { VariablesDetail } from '../../../components/CodeMirrorInput';
import { JobTemplatesAPI } from '../../../api';
import useRequest, { useDismissableError } from '../../../util/useRequest';

function JobTemplateDetail({ i18n, template }) {
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
  } = template;
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(false);
  const [instanceGroups, setInstanceGroups] = useState([]);
  const { id: templateId } = useParams();
  const history = useHistory();

  useEffect(() => {
    (async () => {
      setContentError(null);
      setHasContentLoading(true);
      try {
        const {
          data: { results = [] },
        } = await JobTemplatesAPI.readInstanceGroups(templateId);
        setInstanceGroups(results);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [templateId]);

  const {
    request: deleteJobTemplate,
    isLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await JobTemplatesAPI.destroy(templateId);
      history.push(`/templates`);
    }, [templateId, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);

  const canLaunch =
    summary_fields.user_capabilities && summary_fields.user_capabilities.start;
  const verbosityOptions = [
    { verbosity: 0, details: i18n._(t`0 (Normal)`) },
    { verbosity: 1, details: i18n._(t`1 (Verbose)`) },
    { verbosity: 2, details: i18n._(t`2 (More Verbose)`) },
    { verbosity: 3, details: i18n._(t`3 (Debug)`) },
    { verbosity: 4, details: i18n._(t`4 (Connection Debug)`) },
    { verbosity: 5, details: i18n._(t`5 (WinRM Debug)`) },
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
          {i18n._(t`Enable Privilege Escalation`)}
        </TextListItem>
      )}
      {host_config_key && (
        <TextListItem component={TextListItemVariants.li}>
          {i18n._(t`Allow Provisioning Callbacks`)}
        </TextListItem>
      )}
      {allow_simultaneous && (
        <TextListItem component={TextListItemVariants.li}>
          {i18n._(t`Enable Concurrent Jobs`)}
        </TextListItem>
      )}
      {use_fact_cache && (
        <TextListItem component={TextListItemVariants.li}>
          {i18n._(t`Use Fact Storage`)}
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
        <span> {i18n._(t`(Prompt on launch)`)}</span>
      </Fragment>
    ) : (
      <Link to={`/inventories/${inventorykind}/${id}/details`}>
        {summary_fields.inventory.name}
      </Link>
    );
  };

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={name} dataCy="jt-detail-name" />
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail label={i18n._(t`Job Type`)} value={job_type} />
        {summary_fields.organization ? (
          <Detail
            label={i18n._(t`Organization`)}
            value={
              <Link
                to={`/organizations/${summary_fields.organization.id}/details`}
              >
                {summary_fields.organization.name}
              </Link>
            }
          />
        ) : (
          <DeletedDetail label={i18n._(t`Organization`)} />
        )}
        {summary_fields.inventory ? (
          <Detail
            label={i18n._(t`Inventory`)}
            value={inventoryValue(
              summary_fields.inventory.kind,
              summary_fields.inventory.id
            )}
          />
        ) : (
          !ask_inventory_on_launch && (
            <DeletedDetail label={i18n._(t`Inventory`)} />
          )
        )}
        {summary_fields.project ? (
          <Detail
            label={i18n._(t`Project`)}
            value={
              <Link to={`/projects/${summary_fields.project.id}/details`}>
                {summary_fields.project.name}
              </Link>
            }
          />
        ) : (
          <DeletedDetail label={i18n._(t`Project`)} />
        )}
        <Detail
          label={i18n._(t`Source Control Branch`)}
          value={template.scm_branch}
        />
        <Detail label={i18n._(t`Playbook`)} value={playbook} />
        <Detail label={i18n._(t`Forks`)} value={forks || '0'} />
        <Detail label={i18n._(t`Limit`)} value={limit} />
        <Detail
          label={i18n._(t`Verbosity`)}
          value={verbosityDetails[0].details}
        />
        <Detail label={i18n._(t`Timeout`)} value={timeout || '0'} />
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={modified}
          user={summary_fields.modified_by}
        />
        <Detail
          label={i18n._(t`Show Changes`)}
          value={diff_mode ? i18n._(t`On`) : i18n._(t`Off`)}
        />
        <Detail label={i18n._(t`Job Slicing`)} value={job_slice_count} />
        {host_config_key && (
          <React.Fragment>
            <Detail
              label={i18n._(t`Host Config Key`)}
              value={host_config_key}
            />
            <Detail
              label={i18n._(t`Provisioning Callback URL`)}
              value={generateCallBackUrl}
            />
          </React.Fragment>
        )}
        {webhook_service && (
          <Detail
            label={i18n._(t`Webhook Service`)}
            value={
              webhook_service === 'github'
                ? i18n._(t`GitHub`)
                : i18n._(t`GitLab`)
            }
          />
        )}
        {webhook_receiver && (
          <Detail
            label={i18n._(t`Webhook URL`)}
            value={`${document.location.origin}${webhook_receiver}`}
          />
        )}
        <Detail label={i18n._(t`Webhook Key`)} value={webhook_key} />
        {summary_fields.webhook_credential && (
          <Detail
            label={i18n._(t`Webhook Credential`)}
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
          <Detail label={i18n._(t`Options`)} value={renderOptions} />
        )}
        {summary_fields.credentials && summary_fields.credentials.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Credentials`)}
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
            label={i18n._(t`Labels`)}
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
            label={i18n._(t`Instance Groups`)}
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
            label={i18n._(t`Job Tags`)}
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
            label={i18n._(t`Skip Tags`)}
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
          label={i18n._(t`Variables`)}
        />
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              component={Link}
              to={`/templates/job_template/${templateId}/edit`}
              aria-label={i18n._(t`Edit`)}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
        {canLaunch && (
          <LaunchButton resource={template} aria-label={i18n._(t`Launch`)}>
            {({ handleLaunch }) => (
              <Button variant="secondary" type="submit" onClick={handleLaunch}>
                {i18n._(t`Launch`)}
              </Button>
            )}
          </LaunchButton>
        )}
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={name}
              modalTitle={i18n._(t`Delete Job Template`)}
              onConfirm={deleteJobTemplate}
              isDisabled={isLoading}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {/* Update delete modal to show dependencies https://github.com/ansible/awx/issues/5546 */}
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to delete job template.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export { JobTemplateDetail as _JobTemplateDetail };
export default withI18n()(JobTemplateDetail);
