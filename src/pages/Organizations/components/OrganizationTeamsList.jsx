import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

import {
  DataList, DataListItem, DataListCell, Text,
  TextContent, TextVariants
} from '@patternfly/react-core';

import { I18n, i18nMark } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Link
} from 'react-router-dom';

import Pagination from '../../../components/Pagination';
import DataListToolbar from '../../../components/DataListToolbar';

import {
  parseQueryString,
} from '../../../qs';

const detailWrapperStyle = {
  display: 'grid',
  gridTemplateColumns: 'minmax(70px, max-content) minmax(60px, max-content)',
};

const detailLabelStyle = {
  fontWeight: '700',
  lineHeight: '24px',
  marginRight: '20px',
};

class OrganizationTeamsList extends React.Component {
  columns = [
    { name: i18nMark('Name'), key: 'name', isSortable: true },
  ];

  defaultParams = {
    page: 1,
    page_size: 5,
    order_by: 'name',
  };

  constructor (props) {
    super(props);

    const { page, page_size } = this.readQueryParams();

    this.state = {
      page,
      page_size,
      count: 0,
      sortOrder: 'ascending',
      sortedColumnKey: 'name',
      results: [],
    };

    this.readOrganizationTeamsList = this.readOrganizationTeamsList.bind(this);
    this.handleSetPage = this.handleSetPage.bind(this);
    this.handleSort = this.handleSort.bind(this);
    this.readQueryParams = this.readQueryParams.bind(this);
  }

  componentDidMount () {
    const queryParams = this.readQueryParams();
    try {
      this.readOrganizationTeamsList(queryParams);
    } catch (error) {
      this.setState({ error });
    }
  }

  handleSetPage (pageNumber, pageSize) {
    const { sortOrder, sortedColumnKey } = this.state;
    const page = parseInt(pageNumber, 10);
    const page_size = parseInt(pageSize, 10);
    let order_by = sortedColumnKey;

    // Preserve sort order when paginating
    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    const queryParams = this.readQueryParams({ page, page_size, order_by });

    this.readOrganizationTeamsList(queryParams);
  }

  handleSort (sortedColumnKey, sortOrder) {
    const { page_size } = this.state;

    let order_by = sortedColumnKey;

    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    const queryParams = this.readQueryParams({ order_by, page_size });

    this.readOrganizationTeamsList(queryParams);
  }

  readQueryParams (overrides = {}) {
    const { location } = this.props;
    const { search } = location;

    const searchParams = parseQueryString(search.substring(1));

    return Object.assign({}, this.defaultParams, searchParams, overrides);
  }

  async readOrganizationTeamsList (queryParams) {
    const { match, onReadTeamsList } = this.props;

    const { page, page_size, order_by } = queryParams;

    let sortOrder = 'ascending';
    let sortedColumnKey = order_by;

    if (order_by.startsWith('-')) {
      sortOrder = 'descending';
      sortedColumnKey = order_by.substring(1);
    }

    try {
      const { data:
        { count = 0, results = [] }
      } = await onReadTeamsList(match.params.id, queryParams);
      const pageCount = Math.ceil(count / page_size);

      const stateToUpdate = {
        count,
        page,
        pageCount,
        page_size,
        sortOrder,
        sortedColumnKey,
        results
      };

      this.setState(stateToUpdate);
    } catch (error) {
      this.setState({ error });
    }
  }

  render () {
    const {
      results,
      error,
      count,
      page_size,
      pageCount,
      page,
      sortedColumnKey,
      sortOrder
    } = this.state;
    return (
      <I18n>
        {({ i18n }) => (
          <Fragment>
            {!error && results.length <= 0 && (
              <h1>Loading...</h1> // TODO: replace with proper loading state
            )}
            {error && results.length <= 0 && (
              <Fragment>
                <div>{error.message}</div>
                {error.response && (
                  <div>{error.response.data.detail}</div>
                )}
              </Fragment> // TODO: replace with proper error handling
            )}
            {results.length > 0 && (
              <Fragment>
                <DataListToolbar
                  sortedColumnKey={sortedColumnKey}
                  sortOrder={sortOrder}
                  columns={this.columns}
                  onSearch={() => { }}
                  onSort={this.handleSort}
                />
                <DataList aria-label={i18n._(t`Teams List`)}>
                  {results.map(({ url, id, name }) => (
                    <DataListItem aria-labelledby={i18n._(t`teams-list-item`)} key={id}>
                      <DataListCell>
                        <TextContent style={detailWrapperStyle}>
                          <Link to={{ pathname: url }}>
                            <Text component={TextVariants.h6} style={detailLabelStyle}>{name}</Text>
                          </Link>
                        </TextContent>
                      </DataListCell>
                    </DataListItem>
                  ))}
                </DataList>
                <Pagination
                  count={count}
                  page={page}
                  pageCount={pageCount}
                  page_size={page_size}
                  onSetPage={this.handleSetPage}
                />
              </Fragment>
            )}
          </Fragment>
        )}
      </I18n>
    );
  }
}

OrganizationTeamsList.propTypes = {
  onReadTeamsList: PropTypes.func.isRequired,
};

export default OrganizationTeamsList;
