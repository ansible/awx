import React, { Component, Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { TeamsAPI } from '@api';
import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

import TeamListItem from './TeamListItem';

const QS_CONFIG = getQSConfig('team', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

class TeamsList extends Component {
  constructor(props) {
    super(props);

    this.state = {
      hasContentLoading: true,
      contentError: null,
      deletionError: null,
      teams: [],
      selected: [],
      itemCount: 0,
      actions: null,
    };

    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleTeamDelete = this.handleTeamDelete.bind(this);
    this.handleDeleteErrorClose = this.handleDeleteErrorClose.bind(this);
    this.loadTeams = this.loadTeams.bind(this);
  }

  componentDidMount() {
    this.loadTeams();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.loadTeams();
    }
  }

  handleSelectAll(isSelected) {
    const { teams } = this.state;

    const selected = isSelected ? [...teams] : [];
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

  async handleTeamDelete() {
    const { selected } = this.state;

    this.setState({ hasContentLoading: true });
    try {
      await Promise.all(selected.map(team => TeamsAPI.destroy(team.id)));
    } catch (err) {
      this.setState({ deletionError: err });
    } finally {
      await this.loadTeams();
    }
  }

  async loadTeams() {
    const { location } = this.props;
    const { actions: cachedActions } = this.state;
    const params = parseQueryString(QS_CONFIG, location.search);

    let optionsPromise;
    if (cachedActions) {
      optionsPromise = Promise.resolve({ data: { actions: cachedActions } });
    } else {
      optionsPromise = TeamsAPI.readOptions();
    }

    const promises = Promise.all([TeamsAPI.read(params), optionsPromise]);

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
        teams: results,
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
      teams,
    } = this.state;
    const { match, i18n } = this.props;

    const canAdd =
      actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
    const isAllSelected =
      selected.length > 0 && selected.length === teams.length;

    return (
      <Fragment>
        <PageSection>
          <Card>
            <PaginatedDataList
              contentError={contentError}
              hasContentLoading={hasContentLoading}
              items={teams}
              itemCount={itemCount}
              pluralizedItemName={i18n._(t`Teams`)}
              qsConfig={QS_CONFIG}
              onRowClick={this.handleSelect}
              toolbarSearchColumns={[
                {
                  name: i18n._(t`Name`),
                  key: 'name',
                  isDefault: true,
                },
                {
                  name: i18n._(t`Organization Name`),
                  key: 'organization__name',
                },
                {
                  name: i18n._(t`Created By (Username)`),
                  key: 'created_by__username',
                },
                {
                  name: i18n._(t`Modified By (Username)`),
                  key: 'modified_by__username',
                },
              ]}
              toolbarSortColumns={[
                {
                  name: i18n._(t`Name`),
                  key: 'name',
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
                      onDelete={this.handleTeamDelete}
                      itemsToDelete={selected}
                      pluralizedItemName={i18n._(t`Teams`)}
                    />,
                    canAdd ? (
                      <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
                    ) : null,
                  ]}
                />
              )}
              renderItem={o => (
                <TeamListItem
                  key={o.id}
                  team={o}
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
          {i18n._(t`Failed to delete one or more teams.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      </Fragment>
    );
  }
}

export { TeamsList as _TeamsList };
export default withI18n()(withRouter(TeamsList));
