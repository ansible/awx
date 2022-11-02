import React from 'react';
import { useHistory, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import {
  Toolbar,
  ToolbarContent,
  ToolbarItem,
  ToolbarToggleGroup,
  Tooltip,
  Button,
} from '@patternfly/react-core';
import { SearchIcon } from '@patternfly/react-icons';
import Search from 'components/Search';
import {
  parseQueryString,
  mergeParams,
  removeParams,
  updateQueryString,
} from 'util/qs';
import { isJobRunning } from 'util/jobs';

const SearchToolbarContent = styled(ToolbarContent)`
  padding-left: 0px !important;
  padding-right: 0px !important;
`;

function JobOutputSearch({
  qsConfig,
  job,
  eventRelatedSearchableKeys,
  eventSearchableKeys,
  scrollToEnd,
  isFollowModeEnabled,
  setIsFollowModeEnabled,
}) {
  const location = useLocation();
  const history = useHistory();

  const handleSearch = (key, value) => {
    const params = parseQueryString(qsConfig, location.search);
    const qs = updateQueryString(
      qsConfig,
      location.search,
      mergeParams(params, { [key]: value })
    );
    pushHistoryState(qs);
  };

  const handleReplaceSearch = (key, value) => {
    const qs = updateQueryString(qsConfig, location.search, {
      [key]: value,
    });
    pushHistoryState(qs);
  };

  const handleRemoveSearchTerm = (key, value) => {
    const oldParams = parseQueryString(qsConfig, location.search);
    const updatedParams = removeParams(qsConfig, oldParams, {
      [key]: value,
    });
    const qs = updateQueryString(qsConfig, location.search, updatedParams);
    pushHistoryState(qs);
  };

  const handleRemoveAllSearchTerms = () => {
    const oldParams = parseQueryString(qsConfig, location.search);
    Object.keys(oldParams).forEach((key) => {
      oldParams[key] = null;
    });
    const qs = updateQueryString(qsConfig, location.search, oldParams);
    pushHistoryState(qs);
  };

  const pushHistoryState = (qs) => {
    const { pathname } = history.location;
    history.push(qs ? `${pathname}?${qs}` : pathname);
  };

  const handleFollowToggle = () => {
    if (isFollowModeEnabled) {
      setIsFollowModeEnabled(false);
    } else {
      setIsFollowModeEnabled(true);
      scrollToEnd();
    }
  };

  const columns = [
    {
      name: t`Stdout`,
      key: 'stdout__icontains',
      isDefault: true,
    },
  ];

  if (job.type !== 'system_job' && job.type !== 'inventory_update') {
    columns.push({
      name: t`Event`,
      key: 'or__event',
      options: [
        ['debug', t`Debug`],
        ['deprecated', t`Deprecated`],
        ['error', t`Error`],
        ['runner_on_file_diff', t`File Difference`],
        ['playbook_on_setup', t`Gathering Facts`],
        ['runner_on_async_failed', t`Host Async Failure`],
        ['runner_on_async_ok', t`Host Async OK`],
        ['runner_on_failed', t`Host Failed`],
        ['runner_on_error', t`Host Failure`],
        ['runner_on_ok', t`Host OK`],
        ['runner_on_async_poll', t`Host Polling`],
        ['runner_retry', t`Host Retry`],
        ['runner_on_skipped', t`Host Skipped`],
        ['runner_on_start', t`Host Started`],
        ['runner_on_unreachable', t`Host Unreachable`],
        ['playbook_on_include', t`Including File`],
        ['runner_item_on_failed', t`Item Failed`],
        ['runner_item_on_ok', t`Item OK`],
        ['runner_item_on_skipped', t`Item Skipped`],
        ['playbook_on_no_hosts_matched', t`No Hosts Matched`],
        ['playbook_on_no_hosts_remaining', t`No Hosts Remaining`],
        ['runner_on_no_hosts', t`No Hosts Remaining`],
        ['playbook_on_play_start', t`Play Started`],
        ['playbook_on_stats', t`Playbook Complete`],
        ['playbook_on_start', t`Playbook Started`],
        ['playbook_on_notify', t`Running Handlers`],
        ['system_warning', t`System Warning`],
        ['playbook_on_task_start', t`Task Started`],
        ['playbook_on_vars_prompt', t`Variables Prompted`],
        ['verbose', t`Verbose`],
        ['warning', t`Warning`],
      ],
    });
  }
  columns.push({ name: t`Advanced`, key: 'advanced' });
  const isDisabled = isJobRunning(job.status);

  return (
    <Toolbar
      id="job_output-toolbar"
      clearAllFilters={handleRemoveAllSearchTerms}
      collapseListedFiltersBreakpoint="lg"
      clearFiltersButtonText={t`Clear all filters`}
      ouiaId="job-output-toolbar"
    >
      <SearchToolbarContent>
        <ToolbarToggleGroup toggleIcon={<SearchIcon />} breakpoint="lg">
          <ToolbarItem variant="search-filter">
            {isDisabled ? (
              <Tooltip content={t`Search is disabled while the job is running`}>
                <Search
                  qsConfig={qsConfig}
                  columns={columns}
                  searchableKeys={eventSearchableKeys}
                  relatedSearchableKeys={eventRelatedSearchableKeys}
                  onSearch={handleSearch}
                  onReplaceSearch={handleReplaceSearch}
                  onShowAdvancedSearch={() => {}}
                  onRemove={handleRemoveSearchTerm}
                  isDisabled
                />
              </Tooltip>
            ) : (
              <Search
                qsConfig={qsConfig}
                columns={columns}
                searchableKeys={eventSearchableKeys}
                relatedSearchableKeys={eventRelatedSearchableKeys}
                onSearch={handleSearch}
                onReplaceSearch={handleReplaceSearch}
                onShowAdvancedSearch={() => {}}
                onRemove={handleRemoveSearchTerm}
              />
            )}
          </ToolbarItem>
        </ToolbarToggleGroup>
        {isJobRunning(job.status) ? (
          <Button
            variant={isFollowModeEnabled ? 'secondary' : 'primary'}
            onClick={handleFollowToggle}
          >
            {isFollowModeEnabled ? t`Unfollow` : t`Follow`}
          </Button>
        ) : null}
      </SearchToolbarContent>
    </Toolbar>
  );
}

export default JobOutputSearch;
