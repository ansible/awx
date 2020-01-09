import React, { Component, Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { HostsAPI } from '@api';
import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

import HostListItem from './HostListItem';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

class HostsList extends Component {
  constructor(props) {
    super(props);

    this.state = {
      hasContentLoading: true,
      contentError: null,
      deletionError: null,
      hosts: [],
      selected: [],
      itemCount: 0,
      actions: null,
      toggleError: false,
      toggleLoading: null,
    };

    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleHostDelete = this.handleHostDelete.bind(this);
    this.handleDeleteErrorClose = this.handleDeleteErrorClose.bind(this);
    this.loadActions = this.loadActions.bind(this);
    this.loadHosts = this.loadHosts.bind(this);
    this.handleHostToggle = this.handleHostToggle.bind(this);
    this.handleHostToggleErrorClose = this.handleHostToggleErrorClose.bind(
      this
    );
  }

  componentDidMount() {
    this.loadHosts();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.loadHosts();
    }
  }

  handleSelectAll(isSelected) {
    const { hosts } = this.state;

    const selected = isSelected ? [...hosts] : [];
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

  handleHostToggleErrorClose() {
    this.setState({ toggleError: false });
  }

  async handleHostDelete() {
    const { selected } = this.state;

    this.setState({ hasContentLoading: true });
    try {
      await Promise.all(selected.map(host => HostsAPI.destroy(host.id)));
    } catch (err) {
      this.setState({ deletionError: err });
    } finally {
      await this.loadHosts();
    }
  }

  async handleHostToggle(hostToToggle) {
    const { hosts } = this.state;
    this.setState({ toggleLoading: hostToToggle.id });
    try {
      const { data: updatedHost } = await HostsAPI.update(hostToToggle.id, {
        enabled: !hostToToggle.enabled,
      });
      this.setState({
        hosts: hosts.map(host =>
          host.id === updatedHost.id ? updatedHost : host
        ),
      });
    } catch (err) {
      this.setState({ toggleError: true });
    } finally {
      this.setState({ toggleLoading: null });
    }
  }

  async loadActions() {
    const { actions: cachedActions } = this.state;
    let optionsPromise;
    if (cachedActions) {
      optionsPromise = Promise.resolve({ data: { actions: cachedActions } });
    } else {
      optionsPromise = HostsAPI.readOptions();
    }

    return optionsPromise;
  }

  async loadHosts() {
    const { location } = this.props;
    const params = parseQueryString(QS_CONFIG, location.search);

    const promises = Promise.all([HostsAPI.read(params), this.loadActions()]);

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
        hosts: results,
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
      hosts,
      toggleLoading,
      toggleError,
    } = this.state;
    const { match, i18n } = this.props;

    const canAdd =
      actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
    const isAllSelected =
      selected.length > 0 && selected.length === hosts.length;

    return (
      <Fragment>
        <PageSection>
          <Card>
            <PaginatedDataList
              contentError={contentError}
              hasContentLoading={hasContentLoading}
              items={hosts}
              itemCount={itemCount}
              pluralizedItemName={i18n._(t`Hosts`)}
              qsConfig={QS_CONFIG}
              onRowClick={this.handleSelect}
              toolbarSearchColumns={[
                {
                  name: i18n._(t`Name`),
                  key: 'name',
                  isDefault: true,
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
                      onDelete={this.handleHostDelete}
                      itemsToDelete={selected}
                      pluralizedItemName={i18n._(t`Hosts`)}
                    />,
                    canAdd ? (
                      <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
                    ) : null,
                  ]}
                />
              )}
              renderItem={o => (
                <HostListItem
                  key={o.id}
                  host={o}
                  detailUrl={`${match.url}/${o.id}`}
                  isSelected={selected.some(row => row.id === o.id)}
                  onSelect={() => this.handleSelect(o)}
                  toggleHost={this.handleHostToggle}
                  toggleLoading={toggleLoading === o.id}
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
        {toggleError && !toggleLoading && (
          <AlertModal
            variant="danger"
            title={i18n._(t`Error!`)}
            isOpen={toggleError && !toggleLoading}
            onClose={this.handleHostToggleErrorClose}
          >
            {i18n._(t`Failed to toggle host.`)}
            <ErrorDetail error={toggleError} />
          </AlertModal>
        )}
        {deletionError && (
          <AlertModal
            isOpen={deletionError}
            variant="danger"
            title={i18n._(t`Error!`)}
            onClose={this.handleDeleteErrorClose}
          >
            {i18n._(t`Failed to delete one or more hosts.`)}
            <ErrorDetail error={deletionError} />
          </AlertModal>
        )}
      </Fragment>
    );
  }
}

export { HostsList as _HostsList };
export default withI18n()(withRouter(HostsList));
