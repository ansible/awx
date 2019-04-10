import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import {
  DataList,
  DataListItem,
  DataListCell,
  Text,
  TextContent,
  TextVariants,
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';
import { I18n, i18nMark } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import { withRouter, Link } from 'react-router-dom';

import Pagination from '../../../components/Pagination';
import DataListToolbar from '../../../components/DataListToolbar';

import { encodeQueryString } from '../../../qs';

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

    this.state = {
      error: null,
    };

    this.handleSetPage = this.handleSetPage.bind(this);
    this.handleSort = this.handleSort.bind(this);
  }

  getPageCount () {
    const { itemCount, queryParams: { page_size } } = this.props;
    return Math.ceil(itemCount / page_size);
  }

  getSortOrder () {
    const { queryParams } = this.props;
    if (queryParams.order_by && queryParams.order_by.startsWith('-')) {
      return 'descending';
    }
    return 'ascending';
  }

  handleSetPage (pageNumber, pageSize) {
    this.pushHistoryState({
      page: pageNumber,
      page_size: pageSize,
    });
  }

  handleSort (sortedColumnKey, sortOrder) {
    this.pushHistoryState({
      order_by: sortOrder === 'ascending' ? sortedColumnKey : `-${sortedColumnKey}`,
    });
  }

  pushHistoryState (params) {
    const { history } = this.props;
    const { pathname } = history.location;
    const qs = encodeQueryString(params);
    history.push(`${pathname}?${qs}`);
  }

  render () {
    const { teams, itemCount, queryParams } = this.props;
    const { error } = this.state;
    return (
      <I18n>
        {({ i18n }) => (
          <Fragment>
            {error && (
              <Fragment>
                <div>{error.message}</div>
                {error.response && (
                  <div>{error.response.data.detail}</div>
                )}
              </Fragment> // TODO: replace with proper error handling
            )}
            {teams.length === 0 ? (
              <EmptyState>
                <EmptyStateIcon icon={CubesIcon} />
                <Title size="lg">
                  <Trans>No Teams Found</Trans>
                </Title>
                <EmptyStateBody>
                  <Trans>Please add a team to populate this list</Trans>
                </EmptyStateBody>
              </EmptyState>
            ) : (
              <Fragment>
                <DataListToolbar
                  sortedColumnKey={queryParams.sort_by}
                  sortOrder={this.getSortOrder()}
                  columns={this.columns}
                  onSearch={() => { }}
                  onSort={this.handleSort}
                />
                <DataList aria-label={i18n._(t`Teams List`)}>
                  {teams.map(({ url, id, name }) => (
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
                  count={itemCount}
                  page={queryParams.page}
                  pageCount={this.getPageCount()}
                  page_size={queryParams.page_size}
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

const Item = PropTypes.shape({
  id: PropTypes.number.isRequired,
  url: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
});

const QueryParams = PropTypes.shape({
  page: PropTypes.number,
  page_size: PropTypes.number,
  order_by: PropTypes.string,
});

OrganizationTeamsList.propTypes = {
  teams: PropTypes.arrayOf(Item).isRequired,
  itemCount: PropTypes.number.isRequired,
  queryParams: QueryParams.isRequired
};

export { OrganizationTeamsList as _OrganizationTeamsList };
export default withRouter(OrganizationTeamsList);
