import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Title } from '@patternfly/react-core';
import { DetailList, Detail } from '@components/DetailList';
import HorizontalSeparator from '@components/HorizontalSeparator';

function JobTemplatePreviewStep({ i18n, jobTemplate, linkType }) {
  let linkTypeValue;

  switch (linkType) {
    case 'success':
      linkTypeValue = i18n._(t`On Success`);
      break;
    case 'failure':
      linkTypeValue = i18n._(t`On Failure`);
      break;
    case 'always':
      linkTypeValue = i18n._(t`Always`);
      break;
    default:
      break;
  }

  return (
    <div>
      <Title headingLevel="h1" size="xl">
        {i18n._(t`Job Template Node`)}
      </Title>
      <HorizontalSeparator />
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={jobTemplate.name} />
        <Detail
          label={i18n._(t`Description`)}
          value={jobTemplate.description}
        />
        {/* <Detail label={i18n._(t`Job Type`)} value={job_type} />

        {summary_fields.inventory ? (
          <Detail
            label={i18n._(t`Inventory`)}
            value={inventoryValue(
              summary_fields.inventory.kind,
              summary_fields.inventory.id
            )}
          />
        ) : (
          !ask_inventory_on_launch &&
          renderMissingDataDetail(i18n._(t`Inventory`))
        )}
        {summary_fields.project ? (
          <Detail
            label={i18n._(t`Project`)}
            value={
              <Link to={`/projects/${summary_fields.project.id}/details`}>
                {summary_fields.project
                  ? summary_fields.project.name
                  : i18n._(t`Deleted`)}
              </Link>
            }
          />
        ) : (
          renderMissingDataDetail(i18n._(t`Project`))
        )}
        <Detail label={i18n._(t`Playbook`)} value={playbook} />
        <Detail label={i18n._(t`Forks`)} value={forks || '0'} />
        <Detail label={i18n._(t`Limit`)} value={limit} />
        <Detail
          label={i18n._(t`Verbosity`)}
          value={verbosityDetails[0].details}
        />
        <Detail label={i18n._(t`Timeout`)} value={timeout || '0'} />
        {createdBy && (
          <Detail
            label={i18n._(t`Created`)}
            value={createdBy} // TODO: link to user in users
          />
        )}
        {modifiedBy && (
          <Detail
            label={i18n._(t`Last Modified`)}
            value={modifiedBy} // TODO: link to user in users
          />
        )}
        <Detail
          label={i18n._(t`Show Changes`)}
          value={diff_mode ? 'On' : 'Off'}
        />
        <Detail label={i18n._(t` Job Slicing`)} value={job_slice_count} />
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
        {renderOptionsField && (
          <Detail label={i18n._(t`Options`)} value={renderOptions} />
        )}
        {summary_fields.credentials &&
          summary_fields.credentials.length > 0 && (
            <Detail
              fullWidth
              label={i18n._(t`Credentials`)}
              value={
                <ChipGroup numChips={5}>
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
        {instanceGroups.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Instance Groups`)}
            value={
              <ChipGroup numChips={5}>
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
            label={i18n._(t`Job tags`)}
            value={
              <ChipGroup numChips={5}>
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
            label={i18n._(t`Skip tags`)}
            value={
              <ChipGroup numChips={5}>
                {skip_tags.split(',').map(skipTag => (
                  <Chip key={skipTag} isReadOnly>
                    {skipTag}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )} */}
        <Detail label={i18n._(t`Run`)} value={linkTypeValue} />
      </DetailList>
    </div>
  );
}

export default withI18n()(JobTemplatePreviewStep);
