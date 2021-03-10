import React, { useCallback, useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { useLocation } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';

import { SystemJobTemplatesAPI } from '../../../api';
import AlertModal from '../../../components/AlertModal';
import DatalistToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import { useConfig } from '../../../contexts/Config';
import { parseQueryString, getQSConfig } from '../../../util/qs';
import useRequest from '../../../util/useRequest';

import ManagementJobListItem from './ManagementJobListItem';

const QS_CONFIG = getQSConfig('system_job_templates', {
  page: 1,
  page_size: 20,
});

const buildSearchKeys = options => {
  const actions = options?.data?.actions?.GET || {};
  const searchableKeys = Object.keys(actions).filter(
    key => actions[key].filterable
  );
  const relatedSearchableKeys = options?.data?.related_search_fields || [];

  return { searchableKeys, relatedSearchableKeys };
};

const loadManagementJobs = async search => {
  const params = parseQueryString(QS_CONFIG, search);
  const [
    {
      data: { results: items, count },
    },
    options,
  ] = await Promise.all([
    SystemJobTemplatesAPI.read(params),
    SystemJobTemplatesAPI.readOptions(),
  ]);

  return { items, count, options };
};

function ManagementJobList({ i18n }) {
  const { search } = useLocation();
  const { me } = useConfig();
  const [launchError, setLaunchError] = useState(null);

  const {
    request,
    error = false,
    isLoading = true,
    result: { options = {}, items = [], count = 0 },
  } = useRequest(
    useCallback(async () => loadManagementJobs(search), [search]),
    {}
  );

  useEffect(() => {
    request();
  }, [request]);

  const { searchableKeys, relatedSearchableKeys } = buildSearchKeys(options);

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            qsConfig={QS_CONFIG}
            contentError={error}
            hasContentLoading={isLoading}
            items={items}
            itemCount={count}
            pluralizedItemName={i18n._(t`Management Jobs`)}
            emptyContentMessage={' '}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name__icontains',
                isDefault: true,
              },
            ]}
            renderToolbar={props => (
              <DatalistToolbar
                {...props}
                showSelectAll={false}
                qsConfig={QS_CONFIG}
              />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{i18n._(t`Name`)}</HeaderCell>
                <HeaderCell>{i18n._(t`Description`)}</HeaderCell>
                <HeaderCell>{i18n._(t`Actions`)}</HeaderCell>
              </HeaderRow>
            }
            renderRow={({ id, name, description, job_type }) => (
              <ManagementJobListItem
                key={id}
                id={id}
                name={name}
                jobType={job_type}
                description={description}
                isSuperUser={me?.is_superuser}
                isPrompted={['cleanup_activitystream', 'cleanup_jobs'].includes(
                  job_type
                )}
                onLaunchError={setLaunchError}
              />
            )}
          />
        </Card>
      </PageSection>
      <AlertModal
        isOpen={Boolean(launchError)}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={() => setLaunchError(null)}
      >
        {i18n._(t`Failed to launch job.`)}
        <ErrorDetail error={launchError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(ManagementJobList);
