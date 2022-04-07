import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useHistory } from 'react-router-dom';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import {
  Card,
  PageSection,
  PageSectionVariants,
  SelectGroup,
  Select as PFSelect,
  SelectVariant,
  SelectOption,
  Title,
} from '@patternfly/react-core';

import DatalistToolbar from 'components/DataListToolbar';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  getSearchableKeys,
} from 'components/PaginatedTable';
import useRequest from 'hooks/useRequest';
import useTitle from 'hooks/useTitle';
import { getQSConfig, parseQueryString, updateQueryString } from 'util/qs';
import { ActivityStreamAPI } from 'api';

import ActivityStreamListItem from './ActivityStreamListItem';

const Select = styled(PFSelect)`
  && {
    width: auto;
    white-space: nowrap;
    max-height: 480px;
  }
`;

function ActivityStream() {
  const { light } = PageSectionVariants;

  const [isTypeDropdownOpen, setIsTypeDropdownOpen] = useState(false);
  const location = useLocation();
  const history = useHistory();
  useTitle(t`Activity Stream`);
  const urlParams = new URLSearchParams(location.search);

  const activityStreamType = urlParams.get('type') || 'all';

  let typeParams = {};

  if (activityStreamType !== 'all') {
    typeParams = {
      or__object1__in: activityStreamType,
      or__object2__in: activityStreamType,
    };
  }

  const QS_CONFIG = getQSConfig(
    'activity_stream',
    {
      page: 1,
      page_size: 20,
      order_by: '-timestamp',
    },
    ['id', 'page', 'page_size']
  );

  const {
    result: { results, count, relatedSearchableKeys, searchableKeys },
    error: contentError,
    isLoading,
    request: fetchActivityStream,
  } = useRequest(
    useCallback(
      async () => {
        const params = parseQueryString(QS_CONFIG, location.search);
        const [response, actionsResponse] = await Promise.all([
          ActivityStreamAPI.read({ ...params, ...typeParams }),
          ActivityStreamAPI.readOptions(),
        ]);
        return {
          results: response.data.results,
          count: response.data.count,
          relatedSearchableKeys: (
            actionsResponse?.data?.related_search_fields || []
          ).map((val) => val.slice(0, -8)),
          searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
        };
      },
      [location] // eslint-disable-line react-hooks/exhaustive-deps
    ),
    {
      results: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );
  useEffect(() => {
    fetchActivityStream();
  }, [fetchActivityStream]);

  const pushHistoryState = (urlParamsToAdd) => {
    const pageOneQs = updateQueryString(QS_CONFIG, location.search, {
      page: 1,
    });
    const qs = updateQueryString(null, pageOneQs, {
      type: urlParamsToAdd.get('type'),
    });

    history.push(qs ? `${location.pathname}?${qs}` : location.pathname);
  };

  return (
    <>
      <PageSection
        variant={light}
        className="pf-m-condensed"
        style={{ display: 'flex', justifyContent: 'space-between' }}
      >
        <Title size="2xl" headingLevel="h2" data-cy="screen-title">
          {t`Activity Stream`}
        </Title>
        <span id="grouped-type-select-id" hidden>
          {t`Activity Stream type selector`}
        </span>
        <Select
          variant={SelectVariant.single}
          aria-labelledby="grouped-type-select-id"
          typeAheadAriaLabel={t`Select an activity type`}
          className="activityTypeSelect"
          onToggle={setIsTypeDropdownOpen}
          onSelect={(event, selection) => {
            if (selection) {
              urlParams.set('type', selection);
            }
            setIsTypeDropdownOpen(false);
            pushHistoryState(urlParams);
          }}
          selections={activityStreamType}
          isOpen={isTypeDropdownOpen}
          isGrouped
          noResultsFoundText={t`No results found`}
          ouiaId="activity-type-select"
        >
          <SelectGroup label={t`Views`} key="views">
            <SelectOption key="all_activity" value="all">
              {t`Dashboard (all activity)`}
            </SelectOption>
            <SelectOption key="jobs" value="job">
              {t`Jobs`}
            </SelectOption>
            <SelectOption key="schedules" value="schedule">
              {t`Schedules`}
            </SelectOption>
            <SelectOption key="workflow_approvals" value="workflow_approval">
              {t`Workflow Approvals`}
            </SelectOption>
          </SelectGroup>
          <SelectGroup label={t`Resources`} key="resources">
            <SelectOption
              key="templates"
              value="job_template,workflow_job_template,workflow_job_template_node"
            >
              {t`Templates`}
            </SelectOption>
            <SelectOption key="credentials" value="credential">
              {t`Credentials`}
            </SelectOption>
            <SelectOption key="projects" value="project">
              {t`Projects`}
            </SelectOption>
            <SelectOption key="inventories" value="inventory">
              {t`Inventories`}
            </SelectOption>
            <SelectOption key="hosts" value="host">
              {t`Hosts`}
            </SelectOption>
          </SelectGroup>
          <SelectGroup label={t`Access`} key="access">
            <SelectOption key="organizations" value="organization">
              {t`Organizations`}
            </SelectOption>
            <SelectOption key="users" value="user">
              {t`Users`}
            </SelectOption>
            <SelectOption key="teams" value="team">
              {t`Teams`}
            </SelectOption>
          </SelectGroup>
          <SelectGroup label={t`Administration`} key="administration">
            <SelectOption key="credential_types" value="credential_type">
              {t`Credential Types`}
            </SelectOption>
            <SelectOption
              key="notification_templates"
              value="notification_template"
            >
              {t`Notification Templates`}
            </SelectOption>
            <SelectOption
              key="instance"
              value="instance"
            >{t`Instances`}</SelectOption>
            <SelectOption key="instance_groups" value="instance_group">
              {t`Instance Groups`}
            </SelectOption>
            <SelectOption
              key="applications"
              value="o_auth2_application,o_auth2_access_token"
            >
              {t`Applications & Tokens`}
            </SelectOption>
            <SelectOption
              key="execution_environments"
              value="execution_environment"
            >
              {t`Execution Environments`}
            </SelectOption>
          </SelectGroup>
          <SelectGroup label={t`Settings`} key="settings">
            <SelectOption key="settings" value="setting">
              {t`Settings`}
            </SelectOption>
          </SelectGroup>
        </Select>
      </PageSection>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={isLoading}
            items={results}
            itemCount={count}
            pluralizedItemName={t`Events`}
            qsConfig={QS_CONFIG}
            toolbarSearchColumns={[
              {
                name: t`Keyword`,
                key: 'search',
                isDefault: true,
              },
              {
                name: t`Initiated by (username)`,
                key: 'actor__username__icontains',
              },
            ]}
            toolbarSortColumns={[
              {
                name: t`Time`,
                key: 'timestamp',
              },
              {
                name: t`Initiated by`,
                key: 'actor__username',
              },
            ]}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="timestamp">{t`Time`}</HeaderCell>
                <HeaderCell sortKey="actor__username">
                  {t`Initiated by`}
                </HeaderCell>
                <HeaderCell>{t`Event`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderToolbar={(props) => (
              <DatalistToolbar {...props} qsConfig={QS_CONFIG} />
            )}
            renderRow={(streamItem, index) => (
              <ActivityStreamListItem key={index} streamItem={streamItem} />
            )}
          />
        </Card>
      </PageSection>
    </>
  );
}

export default ActivityStream;
