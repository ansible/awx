import React, { useCallback, useEffect, useState } from 'react';
import { t } from '@lingui/macro';

import { useLocation } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';

import { SystemJobTemplatesAPI } from 'api';
import AlertModal from 'components/AlertModal';
import DatalistToolbar from 'components/DataListToolbar';
import ErrorDetail from 'components/ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  getSearchableKeys,
} from 'components/PaginatedTable';
import { useConfig } from 'contexts/Config';
import { parseQueryString, getQSConfig } from 'util/qs';
import useRequest from 'hooks/useRequest';

import ManagementJobListItem from './ManagementJobListItem';

const QS_CONFIG = getQSConfig('system_job_templates', {
  page: 1,
  page_size: 20,
});

const buildSearchKeys = (options) => {
  const actions = options?.data?.actions?.GET || {};
  const searchableKeys = getSearchableKeys(actions);

  const relatedSearchableKeys = (
    options?.data?.related_search_fields || []
  ).map((val) => val.slice(0, -8));

  return { searchableKeys, relatedSearchableKeys };
};

const loadManagementJobs = async (search) => {
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

function ManagementJobList() {
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
            pluralizedItemName={t`Management Jobs`}
            emptyContentMessage={' '}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            toolbarSearchColumns={[
              {
                name: t`Name`,
                key: 'name__icontains',
                isDefault: true,
              },
            ]}
            renderToolbar={(props) => (
              <DatalistToolbar {...props} qsConfig={QS_CONFIG} />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Description`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
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
        title={t`Error!`}
        onClose={() => setLaunchError(null)}
      >
        {t`Failed to launch job.`}
        <ErrorDetail error={launchError} />
      </AlertModal>
    </>
  );
}

export default ManagementJobList;
