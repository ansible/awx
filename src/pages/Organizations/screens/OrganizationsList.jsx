import React, {
  Component,
  Fragment
} from 'react';
import {
  withRouter
} from 'react-router-dom';

import { I18n, i18nMark } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import {
  Card,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
  PageSection,
  PageSectionVariants,
  Title,
  Button
} from '@patternfly/react-core';

import { CubesIcon } from '@patternfly/react-icons';

import { withNetwork } from '../../../contexts/Network';

import DataListToolbar from '../../../components/DataListToolbar';
import OrganizationListItem from '../components/OrganizationListItem';
import Pagination from '../../../components/Pagination';
import AlertModal from '../../../components/AlertModal';

import {
  encodeQueryString,
  parseQueryString,
} from '../../../util/qs';

class OrganizationsList extends Component {
  columns = [
    { name: i18nMark('Name'), key: 'name', isSortable: true },
    { name: i18nMark('Modified'), key: 'modified', isSortable: true, isNumeric: true },
    { name: i18nMark('Created'), key: 'created', isSortable: true, isNumeric: true },
  ];

  defaultParams = {
    page: 1,
    page_size: 5,
    order_by: 'name',
  };

  constructor (props) {
    super(props);

    const { page, page_size } = this.getQueryParams();

    this.state = {
      page,
      page_size,
      sortedColumnKey: 'name',
      sortOrder: 'ascending',
      count: null,
      error: null,
      loading: true,
      results: [],
      selected: [],
      isModalOpen: false,
      orgsToDelete: [],

    };

    this.onSearch = this.onSearch.bind(this);
    this.getQueryParams = this.getQueryParams.bind(this);
    this.onSort = this.onSort.bind(this);
    this.onSetPage = this.onSetPage.bind(this);
    this.onSelectAll = this.onSelectAll.bind(this);
    this.onSelect = this.onSelect.bind(this);
    this.updateUrl = this.updateUrl.bind(this);
    this.fetchOrganizations = this.fetchOrganizations.bind(this);
    this.handleOrgDelete = this.handleOrgDelete.bind(this);
    this.handleOpenOrgDeleteModal = this.handleOpenOrgDeleteModal.bind(this);
    this.handleClearOrgsToDelete = this.handleClearOrgsToDelete.bind(this);
  }

  componentDidMount () {
    const queryParams = this.getQueryParams();
    this.fetchOrganizations(queryParams);
  }

  onSearch () {
    const { sortedColumnKey, sortOrder } = this.state;

    this.onSort(sortedColumnKey, sortOrder);
  }

  onSort (sortedColumnKey, sortOrder) {
    const { page_size } = this.state;

    let order_by = sortedColumnKey;

    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    const queryParams = this.getQueryParams({ order_by, page_size });

    this.fetchOrganizations(queryParams);
  }

  onSetPage (pageNumber, pageSize) {
    const page = parseInt(pageNumber, 10);
    const page_size = parseInt(pageSize, 10);

    const queryParams = this.getQueryParams({ page, page_size });

    this.fetchOrganizations(queryParams);
  }

  onSelectAll (isSelected) {
    const { results } = this.state;

    const selected = isSelected ? results.map(o => o.id) : [];

    this.setState({ selected });
  }

  onSelect (id) {
    const { selected } = this.state;

    const isSelected = selected.includes(id);

    if (isSelected) {
      this.setState({ selected: selected.filter(s => s !== id) });
    } else {
      this.setState({ selected: selected.concat(id) });
    }
  }

  getQueryParams (overrides = {}) {
    const { location } = this.props;
    const { search } = location;

    const searchParams = parseQueryString(search.substring(1));

    return Object.assign({}, this.defaultParams, searchParams, overrides);
  }

  handleClearOrgsToDelete () {
    this.setState({
      isModalOpen: false,
      orgsToDelete: []
    });
    this.onSelectAll();
  }

  handleOpenOrgDeleteModal () {
    const { results, selected } = this.state;
    const warningTitle = i18nMark(`Delete Organization${selected.length > 1 ? 's' : ''}`);
    const warningMsg = i18nMark('Are you sure you want to delete:');

    const orgsToDelete = [];
    results.forEach((result) => {
      selected.forEach((selectedOrg) => {
        if (result.id === selectedOrg) {
          orgsToDelete.push({ name: result.name, id: selectedOrg });
        }
      });
    });
    this.setState({
      orgsToDelete,
      isModalOpen: true,
      warningTitle,
      warningMsg,
      loading: false });
  }

  async handleOrgDelete (event) {
    const { orgsToDelete } = this.state;
    const { api, handleHttpError } = this.props;
    let errorHandled;

    try {
      await Promise.all(orgsToDelete.map((org) => api.destroyOrganization(org.id)));
      this.handleClearOrgsToDelete();
    } catch (err) {
      errorHandled = handleHttpError(err);
    } finally {
      if (!errorHandled) {
        const queryParams = this.getQueryParams();
        this.fetchOrganizations(queryParams);
      }
    }
    event.preventDefault();
  }

  updateUrl (queryParams) {
    const { history, location } = this.props;
    const pathname = '/organizations';
    const search = `?${encodeQueryString(queryParams)}`;

    if (search !== location.search) {
      history.replace({ pathname, search });
    }
  }

  async fetchOrganizations (queryParams) {
    const { api, handleHttpError } = this.props;
    const { page, page_size, order_by } = queryParams;

    let sortOrder = 'ascending';
    let sortedColumnKey = order_by;

    if (order_by.startsWith('-')) {
      sortOrder = 'descending';
      sortedColumnKey = order_by.substring(1);
    }

    this.setState({ error: false, loading: true });

    try {
      const { data } = await api.getOrganizations(queryParams);
      const { count, results } = data;

      const pageCount = Math.ceil(count / page_size);

      const stateToUpdate = {
        count,
        page,
        pageCount,
        page_size,
        sortOrder,
        sortedColumnKey,
        results,
        selected: [],
        loading: false
      };

      // This is in place to track whether or not the initial request
      // return any results.  If it did not, we show the empty state.
      // This will become problematic once search is in play because
      // the first load may have query params (think bookmarked search)
      if (typeof noInitialResults === 'undefined') {
        stateToUpdate.noInitialResults = results.length === 0;
      }

      this.setState(stateToUpdate);
      this.updateUrl(queryParams);
    } catch (err) {
      handleHttpError(err) || this.setState({ error: true, loading: false });
    }
  }

  render () {
    const {
      medium,
    } = PageSectionVariants;
    const {
      count,
      error,
      loading,
      noInitialResults,
      orgsToDelete,
      page,
      pageCount,
      page_size,
      selected,
      sortedColumnKey,
      sortOrder,
      results,
      isModalOpen,
      warningTitle,
      warningMsg,
    } = this.state;
    const { match } = this.props;
    return (
      <PageSection variant={medium}>
        <Card>
          { isModalOpen && (
            <AlertModal
              variant="danger"
              title={warningTitle}
              isOpen={isModalOpen}
              onClose={this.handleClearOrgsToDelete}
              actions={[
                <Button variant="danger" key="delete" aria-label="confirm-delete" onClick={this.handleOrgDelete}>Delete</Button>,
                <Button variant="secondary" key="cancel" aria-label="cancel-delete" onClick={this.handleClearOrgsToDelete}>Cancel</Button>
              ]}
            >
              {warningMsg}
              <br />
              {orgsToDelete.map((org) => (
                <span key={org.id}>
                  <strong>
                    {org.name}
                  </strong>
                  <br />
                </span>
              ))}
              <br />
            </AlertModal>
          )}
          {noInitialResults && (
            <EmptyState>
              <EmptyStateIcon icon={CubesIcon} />
              <Title size="lg">
                <Trans>No Organizations Found</Trans>
              </Title>
              <EmptyStateBody>
                <Trans>Please add an organization to populate this list</Trans>
              </EmptyStateBody>
            </EmptyState>
          ) || (
            <Fragment>
              <DataListToolbar
                addUrl={`${match.url}/add`}
                isAllSelected={selected.length === results.length}
                sortedColumnKey={sortedColumnKey}
                sortOrder={sortOrder}
                columns={this.columns}
                onSearch={this.onSearch}
                onSort={this.onSort}
                onSelectAll={this.onSelectAll}
                onOpenDeleteModal={this.handleOpenOrgDeleteModal}
                disableTrashCanIcon={selected.length === 0}
                showDelete
                showSelectAll
              />
              <I18n>
                {({ i18n }) => (
                  <ul className="pf-c-data-list" aria-label={i18n._(t`Organizations List`)}>
                    { results.map(o => (
                      <OrganizationListItem
                        key={o.id}
                        itemId={o.id}
                        name={o.name}
                        detailUrl={`${match.url}/${o.id}`}
                        memberCount={o.summary_fields.related_field_counts.users}
                        teamCount={o.summary_fields.related_field_counts.teams}
                        isSelected={selected.includes(o.id)}
                        onSelect={() => this.onSelect(o.id, o.name)}
                        onOpenOrgDeleteModal={this.handleOpenOrgDeleteModal}
                      />
                    ))}
                  </ul>
                )}
              </I18n>
              <Pagination
                count={count}
                page={page}
                pageCount={pageCount}
                page_size={page_size}
                onSetPage={this.onSetPage}
              />
              { loading ? <div>loading...</div> : '' }
              { error ? <div>error</div> : '' }
            </Fragment>
          )}
        </Card>
      </PageSection>
    );
  }
}

export { OrganizationsList as _OrganizationsList };
export default withNetwork(withRouter(OrganizationsList));
