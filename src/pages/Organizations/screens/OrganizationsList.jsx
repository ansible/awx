import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Card,
  PageSection,
  PageSectionVariants,
} from '@patternfly/react-core';

import { withNetwork } from '../../../contexts/Network';
import PaginatedDataList, {
  ToolbarDeleteButton,
  ToolbarAddButton
} from '../../../components/PaginatedDataList';
import OrganizationListItem from '../components/OrganizationListItem';
import { getQSConfig, parseNamespacedQueryString } from '../../../util/qs';

const QS_CONFIG = getQSConfig('organization', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

class OrganizationsList extends Component {
  constructor (props) {
    super(props);

    this.state = {
      error: null,
      isLoading: true,
      isInitialized: false,
      organizations: [],
      selected: []
    };

    this.handleSelectAll = this.handleSelectAll.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.fetchOptionsOrganizations = this.fetchOptionsOrganizations.bind(this);
    this.fetchOrganizations = this.fetchOrganizations.bind(this);
    this.handleOrgDelete = this.handleOrgDelete.bind(this);
  }

  componentDidMount () {
    this.fetchOptionsOrganizations();
    this.fetchOrganizations();
  }

  componentDidUpdate (prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.fetchOrganizations();
    }
  }

  handleSelectAll (isSelected) {
    const { organizations } = this.state;

    const selected = isSelected ? [...organizations] : [];
    this.setState({ selected });
  }

  handleSelect (row) {
    const { selected } = this.state;

    if (selected.some(s => s.id === row.id)) {
      this.setState({ selected: selected.filter(s => s.id !== row.id) });
    } else {
      this.setState({ selected: selected.concat(row) });
    }
  }

  async handleOrgDelete () {
    const { selected } = this.state;
    const { api, handleHttpError } = this.props;
    let errorHandled;

    try {
      await Promise.all(selected.map((org) => api.destroyOrganization(org.id)));
      this.setState({
        selected: []
      });
    } catch (err) {
      errorHandled = handleHttpError(err);
    } finally {
      if (!errorHandled) {
        this.fetchOrganizations();
      }
    }
  }

  async fetchOrganizations () {
    const { api, handleHttpError, location } = this.props;
    const params = parseNamespacedQueryString(QS_CONFIG, location.search);

    this.setState({ error: false, isLoading: true });

    try {
      const { data } = await api.getOrganizations(params);
      const { count, results } = data;

      const stateToUpdate = {
        itemCount: count,
        organizations: results,
        selected: [],
        isLoading: false,
        isInitialized: true,
      };

      this.setState(stateToUpdate);
    } catch (err) {
      handleHttpError(err) || this.setState({ error: true, isLoading: false });
    }
  }

  async fetchOptionsOrganizations () {
    const { api } = this.props;

    try {
      const { data } = await api.optionsOrganizations();
      const { actions } = data;

      const stateToUpdate = {
        canAdd: Object.prototype.hasOwnProperty.call(actions, 'POST')
      };

      this.setState(stateToUpdate);
    } catch (err) {
      this.setState({ error: true });
    } finally {
      this.setState({ isLoading: false });
    }
  }

  render () {
    const {
      medium,
    } = PageSectionVariants;
    const {
      canAdd,
      itemCount,
      error,
      isLoading,
      isInitialized,
      selected,
      organizations
    } = this.state;
    const { match, i18n } = this.props;

    const isAllSelected = selected.length === organizations.length;

    return (
      <PageSection variant={medium}>
        <Card>
          {isInitialized && (
            <PaginatedDataList
              items={organizations}
              itemCount={itemCount}
              itemName="organization"
              qsConfig={QS_CONFIG}
              toolbarColumns={[
                { name: i18n._(t`Name`), key: 'name', isSortable: true },
                { name: i18n._(t`Modified`), key: 'modified', isSortable: true, isNumeric: true },
                { name: i18n._(t`Created`), key: 'created', isSortable: true, isNumeric: true },
              ]}
              showSelectAll
              isAllSelected={isAllSelected}
              onSelectAll={this.handleSelectAll}
              additionalControls={[
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={this.handleOrgDelete}
                  itemsToDelete={selected}
                  itemName="Organization"
                />,
                canAdd
                  ? <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
                  : null,
              ]}
              renderItem={(o) => (
                <OrganizationListItem
                  key={o.id}
                  organization={o}
                  detailUrl={`${match.url}/${o.id}`}
                  isSelected={selected.some(row => row.id === o.id)}
                  onSelect={() => this.handleSelect(o)}
                />
              )}
              emptyStateControls={
                canAdd ? <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
                  : null
              }
            />
          )}
          { isLoading ? <div>loading...</div> : '' }
          { error ? <div>error</div> : '' }
        </Card>
      </PageSection>
    );
  }
}

export { OrganizationsList as _OrganizationsList };
export default withI18n()(withNetwork(withRouter(OrganizationsList)));
