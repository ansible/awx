import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Chip } from '@patternfly/react-core';
import { Tr, Td, ExpandableRowContent } from '@patternfly/react-table';
import { RocketIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { ActionsTd, ActionItem } from '../PaginatedTable';
import { LaunchButton, ReLaunchDropDown } from '../LaunchButton';
import StatusLabel from '../StatusLabel';
import { DetailList, Detail, LaunchedByDetail } from '../DetailList';
import ChipGroup from '../ChipGroup';
import CredentialChip from '../CredentialChip';
import { formatDateString } from '../../util/dates';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';

const Dash = styled.span``;
function JobListItem({
  i18n,
  job,
  rowIndex,
  isSelected,
  onSelect,
  showTypeColumn = false,
}) {
  const labelId = `check-action-${job.id}`;
  const [isExpanded, setIsExpanded] = useState(false);

  const jobTypes = {
    project_update: i18n._(t`Source Control Update`),
    inventory_update: i18n._(t`Inventory Sync`),
    job: i18n._(t`Playbook Run`),
    ad_hoc_command: i18n._(t`Command`),
    management_job: i18n._(t`Management Job`),
    workflow_job: i18n._(t`Workflow Job`),
  };

  const { credentials, inventory, labels } = job.summary_fields;

  return (
    <>
      <Tr id={`job-row-${job.id}`}>
        <Td
          expand={{
            rowIndex: job.id,
            isExpanded,
            onToggle: () => setIsExpanded(!isExpanded),
          }}
        />
        <Td
          select={{
            rowIndex,
            isSelected,
            onSelect,
          }}
          dataLabel={i18n._(t`Select`)}
        />
        <Td id={labelId} dataLabel={i18n._(t`Name`)}>
          <span>
            <Link to={`/jobs/${JOB_TYPE_URL_SEGMENTS[job.type]}/${job.id}`}>
              <b>
                {job.id} <Dash>&mdash;</Dash> {job.name}
              </b>
            </Link>
          </span>
        </Td>
        <Td dataLabel={i18n._(t`Status`)}>
          {job.status && <StatusLabel status={job.status} />}
        </Td>
        {showTypeColumn && (
          <Td dataLabel={i18n._(t`Type`)}>{jobTypes[job.type]}</Td>
        )}
        <Td dataLabel={i18n._(t`Start Time`)}>
          {formatDateString(job.started)}
        </Td>
        <Td dataLabel={i18n._(t`Finish Time`)}>
          {job.finished ? formatDateString(job.finished) : ''}
        </Td>
        <ActionsTd dataLabel={i18n._(t`Actions`)}>
          <ActionItem
            visible={
              job.type !== 'system_job' &&
              job.summary_fields?.user_capabilities?.start
            }
            tooltip={
              job.status === 'failed' && job.type === 'job'
                ? i18n._(t`Relaunch using host parameters`)
                : i18n._(t`Relaunch Job`)
            }
          >
            {job.status === 'failed' && job.type === 'job' ? (
              <LaunchButton resource={job}>
                {({ handleRelaunch }) => (
                  <ReLaunchDropDown handleRelaunch={handleRelaunch} />
                )}
              </LaunchButton>
            ) : (
              <LaunchButton resource={job}>
                {({ handleRelaunch }) => (
                  <Button
                    variant="plain"
                    onClick={handleRelaunch}
                    aria-label={i18n._(t`Relaunch`)}
                  >
                    <RocketIcon />
                  </Button>
                )}
              </LaunchButton>
            )}
          </ActionItem>
        </ActionsTd>
      </Tr>
      <Tr isExpanded={isExpanded} id={`expanded-job-row-${job.id}`}>
        <Td colSpan={2} />
        <Td colSpan={showTypeColumn ? 5 : 4}>
          <ExpandableRowContent>
            <DetailList>
              <LaunchedByDetail job={job} i18n={i18n} />
              {credentials && credentials.length > 0 && (
                <Detail
                  fullWidth
                  label={i18n._(t`Credentials`)}
                  value={
                    <ChipGroup numChips={5} totalChips={credentials.length}>
                      {credentials.map(c => (
                        <CredentialChip key={c.id} credential={c} isReadOnly />
                      ))}
                    </ChipGroup>
                  }
                />
              )}
              {labels && labels.count > 0 && (
                <Detail
                  label={i18n._(t`Labels`)}
                  value={
                    <ChipGroup numChips={5} totalChips={labels.results.length}>
                      {labels.results.map(l => (
                        <Chip key={l.id} isReadOnly>
                          {l.name}
                        </Chip>
                      ))}
                    </ChipGroup>
                  }
                />
              )}
              {inventory && (
                <Detail
                  label={i18n._(t`Inventory`)}
                  value={
                    <Link
                      to={
                        inventory.kind === 'smart'
                          ? `/inventories/smart_inventory/${inventory.id}`
                          : `/inventories/inventory/${inventory.id}`
                      }
                    >
                      {inventory.name}
                    </Link>
                  }
                />
              )}
            </DetailList>
          </ExpandableRowContent>
        </Td>
      </Tr>
    </>
  );
}

export { JobListItem as _JobListItem };
export default withI18n()(JobListItem);
