import React, { Component, Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { ProjectsAPI } from '@api';
import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

import ProjectListItem from './ProjectListItem';

const QS_CONFIG = getQSConfig('project', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

class ProjectsList extends Component {
  constructor(props) {
    super(props);

    this.state = {
      hasContentLoading: true,
      contentError: null,
      deletionError: null,
      projects: [],
      selected: [],
      itemCount: 0,
      actions: null,
    };

    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleProjectDelete = this.handleProjectDelete.bind(this);
    this.handleDeleteErrorClose = this.handleDeleteErrorClose.bind(this);
    this.loadProjects = this.loadProjects.bind(this);
  }

  componentDidMount() {
    this.loadProjects();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.loadProjects();
    }
  }

  handleSelectAll(isSelected) {
    const { projects } = this.state;

    const selected = isSelected ? [...projects] : [];
    this.setState({ selected });
  }

  handleSelect(row) {
    const { selected } = this.state;

    if (selected.some(s => s.id === row.id)) {
      this.setState({ selected: selected.filter(s => s.id !== row.id) });
    } else {
      this.setState({ selected: selected.concat(row) });
    }
  }

  handleDeleteErrorClose() {
    this.setState({ deletionError: null });
  }

  async handleProjectDelete() {
    const { selected } = this.state;

    this.setState({ hasContentLoading: true });
    try {
      await Promise.all(
        selected.map(project => ProjectsAPI.destroy(project.id))
      );
    } catch (err) {
      this.setState({ deletionError: err });
    } finally {
      await this.loadProjects();
    }
  }

  async loadProjects() {
    const { location } = this.props;
    const { actions: cachedActions } = this.state;
    const params = parseQueryString(QS_CONFIG, location.search);

    let optionsPromise;
    if (cachedActions) {
      optionsPromise = Promise.resolve({ data: { actions: cachedActions } });
    } else {
      optionsPromise = ProjectsAPI.readOptions();
    }

    const promises = Promise.all([ProjectsAPI.read(params), optionsPromise]);

    this.setState({ contentError: null, hasContentLoading: true });
    try {
      const [
        {
          data: { count, results },
        },
        {
          data: { actions },
        },
      ] = await promises;
      this.setState({
        actions,
        itemCount: count,
        projects: results,
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
      actions,
      itemCount,
      contentError,
      hasContentLoading,
      deletionError,
      selected,
      projects,
    } = this.state;
    const { match, i18n } = this.props;

    const canAdd =
      actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
    const isAllSelected = selected.length === projects.length;

    return (
      <Fragment>
        <PageSection>
          <Card>
            <PaginatedDataList
              contentError={contentError}
              hasContentLoading={hasContentLoading}
              items={projects}
              itemCount={itemCount}
              pluralizedItemName={i18n._(t`Projects`)}
              qsConfig={QS_CONFIG}
              toolbarColumns={[
                {
                  name: i18n._(t`Name`),
                  key: 'name',
                  isSortable: true,
                  isSearchable: true,
                },
                {
                  name: i18n._(t`Modified`),
                  key: 'modified',
                  isSortable: true,
                  isNumeric: true,
                },
                {
                  name: i18n._(t`Created`),
                  key: 'created',
                  isSortable: true,
                  isNumeric: true,
                },
              ]}
              renderToolbar={props => (
                <DataListToolbar
                  {...props}
                  showSelectAll
                  isAllSelected={isAllSelected}
                  onSelectAll={this.handleSelectAll}
                  qsConfig={QS_CONFIG}
                  additionalControls={[
                    <ToolbarDeleteButton
                      key="delete"
                      onDelete={this.handleProjectDelete}
                      itemsToDelete={selected}
                      pluralizedItemName={i18n._(t`Projects`)}
                    />,
                    canAdd ? (
                      <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
                    ) : null,
                  ]}
                />
              )}
              renderItem={o => (
                <ProjectListItem
                  key={o.id}
                  project={o}
                  detailUrl={`${match.url}/${o.id}`}
                  isSelected={selected.some(row => row.id === o.id)}
                  onSelect={() => this.handleSelect(o)}
                />
              )}
              emptyStateControls={
                canAdd ? (
                  <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
                ) : null
              }
            />
          </Card>
        </PageSection>
        <AlertModal
          isOpen={deletionError}
          variant="danger"
          title={i18n._(t`Error!`)}
          onClose={this.handleDeleteErrorClose}
        >
          {i18n._(t`Failed to delete one or more projects.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      </Fragment>
    );
  }
}

export { ProjectsList as _ProjectsList };
export default withI18n()(withRouter(ProjectsList));
