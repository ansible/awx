import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import {
  AdHocCommandsAPI,
  InventoryUpdatesAPI,
  JobsAPI,
  ProjectUpdatesAPI,
  SystemJobsAPI,
  UnifiedJobsAPI,
  WorkflowJobsAPI,
} from '@api';
import AlertModal from '@components/AlertModal';
import DatalistToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

import JobListItem from './JobListItem';

const QS_CONFIG = getQSConfig('job', {
  page: 1,
  page_size: 20,
  order_by: '-finished',
  not__launch_type: 'sync',
});

class JobList extends Component {
  constructor(props) {
    super(props);

    this.state = {
      hasContentLoading: true,
      deletionError: null,
      contentError: null,
      selected: [],
      jobs: [],
      itemCount: 0,
    };
    this.loadJobs = this.loadJobs.bind(this);
    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleJobDelete = this.handleJobDelete.bind(this);
    this.handleDeleteErrorClose = this.handleDeleteErrorClose.bind(this);
  }

  componentDidMount() {
    this.loadJobs();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.loadJobs();
    }
  }

  handleDeleteErrorClose() {
    this.setState({ deletionError: null });
  }

  handleSelectAll(isSelected) {
    const { jobs } = this.state;
    const selected = isSelected ? [...jobs] : [];
    this.setState({ selected });
  }

  handleSelect(item) {
    const { selected } = this.state;
    if (selected.some(s => s.id === item.id)) {
      this.setState({ selected: selected.filter(s => s.id !== item.id) });
    } else {
      this.setState({ selected: selected.concat(item) });
    }
  }

  async handleJobDelete() {
    const { selected, itemCount } = this.state;
    this.setState({ hasContentLoading: true });
    try {
      await Promise.all(
        selected.map(({ type, id }) => {
          let deletePromise;
          switch (type) {
            case 'job':
              deletePromise = JobsAPI.destroy(id);
              break;
            case 'ad_hoc_command':
              deletePromise = AdHocCommandsAPI.destroy(id);
              break;
            case 'system_job':
              deletePromise = SystemJobsAPI.destroy(id);
              break;
            case 'project_update':
              deletePromise = ProjectUpdatesAPI.destroy(id);
              break;
            case 'inventory_update':
              deletePromise = InventoryUpdatesAPI.destroy(id);
              break;
            case 'workflow_job':
              deletePromise = WorkflowJobsAPI.destroy(id);
              break;
            default:
              break;
          }
          return deletePromise;
        })
      );
      this.setState({ itemCount: itemCount - selected.length });
    } catch (err) {
      this.setState({ deletionError: err });
    } finally {
      await this.loadJobs();
    }
  }

  async loadJobs() {
    const { location } = this.props;
    const params = parseQueryString(QS_CONFIG, location.search);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const {
        data: { count, results },
      } = await UnifiedJobsAPI.read(params);
      this.setState({
        itemCount: count,
        jobs: results,
        selected: [],
      });
    } catch (err) {
      this.setState({ contentError: err });
    } finally {
      this.setState({ hasContentLoading: false });
    }
  }

  render() {
    const {
      contentError,
      hasContentLoading,
      deletionError,
      jobs,
      itemCount,
      selected,
    } = this.state;
    const { match, i18n } = this.props;
    const isAllSelected =
      selected.length === jobs.length && selected.length > 0;
    return (
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={jobs}
            itemCount={itemCount}
            pluralizedItemName="Jobs"
            qsConfig={QS_CONFIG}
            toolbarColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isSortable: true,
                isSearchable: true,
              },
              {
                name: i18n._(t`Finished`),
                key: 'finished',
                isSortable: true,
                isNumeric: true,
              },
            ]}
            renderToolbar={props => (
              <DatalistToolbar
                {...props}
                showSelectAll
                showExpandCollapse
                isAllSelected={isAllSelected}
                onSelectAll={this.handleSelectAll}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={this.handleJobDelete}
                    itemsToDelete={selected}
                    pluralizedItemName="Jobs"
                  />,
                ]}
              />
            )}
            renderItem={job => (
              <JobListItem
                key={job.id}
                value={job.name}
                job={job}
                detailUrl={`${match.url}/${job}/${job.id}`}
                onSelect={() => this.handleSelect(job)}
                isSelected={selected.some(row => row.id === job.id)}
              />
            )}
          />
        </Card>
        <AlertModal
          isOpen={deletionError}
          variant="danger"
          title={i18n._(t`Error!`)}
          onClose={this.handleDeleteErrorClose}
        >
          {i18n._(t`Failed to delete one or more jobs.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      </PageSection>
    );
  }
}

export { JobList as _JobList };
export default withI18n()(withRouter(JobList));
