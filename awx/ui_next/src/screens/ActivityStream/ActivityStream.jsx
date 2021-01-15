import React, { Fragment, useState, useEffect, useCallback } from 'react';
import { useLocation, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Card,
  PageSection,
  PageSectionVariants,
  Select,
  SelectVariant,
  SelectOption,
  Title,
} from '@patternfly/react-core';

import DatalistToolbar from '../../components/DataListToolbar';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../components/PaginatedTable';
import useRequest from '../../util/useRequest';
import { getQSConfig, parseQueryString } from '../../util/qs';
import { ActivityStreamAPI } from '../../api';

import ActivityStreamListItem from './ActivityStreamListItem';

function ActivityStream({ i18n }) {
  const { light } = PageSectionVariants;

  const [isTypeDropdownOpen, setIsTypeDropdownOpen] = useState(false);
  const location = useLocation();
  const history = useHistory();
  const urlParams = new URLSearchParams(location.search);

  const activityStreamType = urlParams.get('type');

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
          ).map(val => val.slice(0, -8)),
          searchableKeys: Object.keys(
            actionsResponse.data.actions?.GET || {}
          ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
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

  return (
    <Fragment>
      <PageSection
        variant={light}
        className="pf-m-condensed"
        style={{ display: 'flex', justifyContent: 'space-between' }}
      >
        <Title size="2xl" headingLevel="h2">
          {i18n._(t`Activity Stream`)}
        </Title>
        <Select
          width="250px"
          variant={SelectVariant.single}
          aria-label={i18n._(t`Activity Stream type selector`)}
          className="activityTypeSelect"
          onToggle={setIsTypeDropdownOpen}
          onSelect={(event, selection) => {
            if (selection) {
              urlParams.set('type', selection);
            }
            setIsTypeDropdownOpen(false);
            history.push(`${location.pathname}?${urlParams.toString()}`);
          }}
          selections={activityStreamType}
          isOpen={isTypeDropdownOpen}
        >
          <SelectOption key="all_activity" value="all">
            {i18n._(t`All activity`)}
          </SelectOption>
          <SelectOption key="inventories" value="inventory">
            {i18n._(t`Inventories`)}
          </SelectOption>
          <SelectOption
            key="applications"
            value="o_auth2_application,o_auth2_access_token"
          >
            {i18n._(t`Applications & Tokens`)}
          </SelectOption>
          <SelectOption key="credentials" value="credential">
            {i18n._(t`Credentials`)}
          </SelectOption>
          <SelectOption key="hosts" value="host">
            {i18n._(t`Hosts`)}
          </SelectOption>
          <SelectOption key="inventory_scripts" value="custom_inventory_script">
            {i18n._(t`Inventory Scripts`)}
          </SelectOption>
          <SelectOption key="jobs" value="job">
            {i18n._(t`Jobs`)}
          </SelectOption>
          <SelectOption
            key="notification_templates"
            value="notification_template"
          >
            {i18n._(t`Notification Templates`)}
          </SelectOption>
          <SelectOption key="organizations" value="organization">
            {i18n._(t`Organizations`)}
          </SelectOption>
          <SelectOption key="projects" value="project">
            {i18n._(t`Projects`)}
          </SelectOption>
          <SelectOption key="credential_types" value="credential_type">
            {i18n._(t`Credential Types`)}
          </SelectOption>
          <SelectOption key="schedules" value="schedule">
            {i18n._(t`Schedules`)}
          </SelectOption>
          <SelectOption key="teams" value="team">
            {i18n._(t`Teams`)}
          </SelectOption>
          <SelectOption
            key="templates"
            value="job_template,workflow_job_template,workflow_job_template_node"
          >
            {i18n._(t`Templates`)}
          </SelectOption>
          <SelectOption key="users" value="user">
            {i18n._(t`Users`)}
          </SelectOption>
          <SelectOption key="workflow_approvals" value="workflow_approval">
            {i18n._(t`Workflow Approvals`)}
          </SelectOption>
          <SelectOption key="instance_groups" value="instance_group">
            {i18n._(t`Instance Groups`)}
          </SelectOption>
          <SelectOption key="settings" value="setting">
            {i18n._(t`Settings`)}
          </SelectOption>
        </Select>
      </PageSection>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={isLoading}
            items={results}
            itemCount={count}
            pluralizedItemName={i18n._(t`Events`)}
            qsConfig={QS_CONFIG}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Keyword`),
                key: 'search',
                isDefault: true,
              },
              {
                name: i18n._(t`Initiated by (username)`),
                key: 'actor__username__icontains',
              },
            ]}
            toolbarSortColumns={[
              {
                name: i18n._(t`Time`),
                key: 'timestamp',
              },
              {
                name: i18n._(t`Initiated by`),
                key: 'actor__username',
              },
            ]}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG}>
                <HeaderCell sortKey="timestamp">{i18n._(t`Time`)}</HeaderCell>
                <HeaderCell sortKey="actor__username">
                  {i18n._(t`Initiated by`)}
                </HeaderCell>
                <HeaderCell>{i18n._(t`Event`)}</HeaderCell>
                <HeaderCell>{i18n._(t`Actions`)}</HeaderCell>
              </HeaderRow>
            }
            renderToolbar={props => (
              <DatalistToolbar {...props} qsConfig={QS_CONFIG} />
            )}
            renderRow={streamItem => (
              <ActivityStreamListItem streamItem={streamItem} />
            )}
          />
        </Card>
      </PageSection>
    </Fragment>
  );
}

export default withI18n()(ActivityStream);
