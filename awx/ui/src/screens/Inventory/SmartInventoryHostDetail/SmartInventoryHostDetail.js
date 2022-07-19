import React from 'react';
import { Link } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Host } from 'types';
import { CardBody } from 'components/Card';
import { Detail, DetailList, UserDateDetail } from 'components/DetailList';
import Sparkline from 'components/Sparkline';
import { VariablesDetail } from 'components/CodeEditor';

function SmartInventoryHostDetail({ host }) {
  const {
    created,
    description,
    enabled,
    modified,
    name,
    variables,
    summary_fields: { inventory, recent_jobs, created_by, modified_by },
  } = host;

  const recentPlaybookJobs = recent_jobs?.map((job) => ({
    ...job,
    type: 'job',
  }));

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail label={t`Name`} value={name} />
        <Detail
          label={t`Activity`}
          value={<Sparkline jobs={recentPlaybookJobs} />}
          isEmpty={recentPlaybookJobs?.length === 0}
        />
        <Detail label={t`Description`} value={description} />
        <Detail
          label={t`Inventory`}
          value={
            <Link to={`/inventories/inventory/${inventory?.id}/details`}>
              {inventory?.name}
            </Link>
          }
        />
        <Detail label={t`Enabled`} value={enabled ? t`On` : t`Off`} />
        <UserDateDetail date={created} label={t`Created`} user={created_by} />
        <UserDateDetail
          date={modified}
          label={t`Last modified`}
          user={modified_by}
        />
        <VariablesDetail
          label={t`Variables`}
          rows={4}
          value={variables}
          name="variables"
          dataCy="smart-inventory-host-detail-variables"
        />
      </DetailList>
    </CardBody>
  );
}

SmartInventoryHostDetail.propTypes = {
  host: Host.isRequired,
};

export default SmartInventoryHostDetail;
