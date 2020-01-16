import React, { useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';
import { t } from '@lingui/macro';
import { WorkflowJobTemplatesAPI } from '@api';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { DetailList, Detail } from '@components/DetailList';
import { ChipGroup, Chip } from '@components/Chip';
import { VariablesDetail } from '@components/CodeMirrorInput';

function WorkflowJobTemplateDetails({ i18n, node }) {
  const [workflowJobTemplate, setWorkflowJobTemplate] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [noReadAccess, setNoReadAccess] = useState(false);
  const [contentError, setContentError] = useState(null);

  useEffect(() => {
    async function fetchWorkflowJobTemplate() {
      try {
        const { data } = await WorkflowJobTemplatesAPI.readDetail(
          node.unifiedJobTemplate.id
        );
        setWorkflowJobTemplate(data);
      } catch (err) {
        if (err.response.status === 403) {
          setNoReadAccess(true);
        } else {
          setContentError(err);
        }
      } finally {
        setIsLoading(false);
      }
    }
    fetchWorkflowJobTemplate();
  }, []);

  if (isLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  if (noReadAccess) {
    return (
      <>
        <p>
          <Trans>
            Your account does not have read access to this workflow job template
            so the displayed details will be limited.
          </Trans>
        </p>
        <br />
        <DetailList gutter="sm">
          <Detail
            label={i18n._(t`Node Type`)}
            value={i18n._(t`Workflow Job Template`)}
          />
          <Detail
            label={i18n._(t`Name`)}
            value={node.unifiedJobTemplate.name}
          />
          <Detail
            label={i18n._(t`Description`)}
            value={node.unifiedJobTemplate.description}
          />
        </DetailList>
      </>
    );
  }

  const {
    description,
    extra_vars,
    limit,
    name,
    scm_branch,
    summary_fields,
  } = workflowJobTemplate;

  return (
    <DetailList gutter="sm">
      <Detail
        label={i18n._(t`Node Type`)}
        value={i18n._(t`Workflow Job Template`)}
      />
      <Detail label={i18n._(t`Name`)} value={name} />
      <Detail label={i18n._(t`Description`)} value={description} />
      {summary_fields.organization && (
        <Detail
          label={i18n._(t`Organization`)}
          value={summary_fields.organization.name}
        />
      )}
      {summary_fields.inventory && (
        <Detail
          label={i18n._(t`Inventory`)}
          value={summary_fields.inventory.name}
        />
      )}
      <Detail label={i18n._(t`Limit`)} value={limit} />
      <Detail label={i18n._(t`SCM Branch`)} value={scm_branch} />
      {summary_fields.labels && summary_fields.labels.results.length > 0 && (
        <Detail
          fullWidth
          label={i18n._(t`Labels`)}
          value={
            <ChipGroup numChips={5}>
              {summary_fields.labels.results.map(l => (
                <Chip key={l.id} isReadOnly>
                  {l.name}
                </Chip>
              ))}
            </ChipGroup>
          }
        />
      )}
      <VariablesDetail
        label={i18n._(t`Variables`)}
        value={extra_vars}
        rows={4}
      />
    </DetailList>
  );
}

export default withI18n()(WorkflowJobTemplateDetails);
