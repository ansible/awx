import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Checkbox,
  Toolbar as PFToolbar,
  ToolbarGroup as PFToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';

import styled from 'styled-components';
import ExpandCollapse from '../ExpandCollapse';
import Search from '../Search';
import Sort from '../Sort';
import VerticalSeparator from '../VerticalSeparator';

const AWXToolbar = styled.div`
  --awx-toolbar--BackgroundColor: var(--pf-global--BackgroundColor--light-100);
  --awx-toolbar--BorderColor: #ebebeb;
  --awx-toolbar--BorderWidth: var(--pf-global--BorderWidth--sm);

  --pf-global--target-size--MinHeight: 0;
  --pf-global--target-size--MinWidth: 0;
  --pf-global--FontSize--md: 14px;

  border-bottom: var(--awx-toolbar--BorderWidth) solid var(--awx-toolbar--BorderColor);
  background-color: var(--awx-toolbar--BackgroundColor);
  display: flex;
  min-height: 70px;
  flex-grow: 1;
`;

const Toolbar = styled(PFToolbar)`
  flex-grow: 1;
  margin-left: ${props => (props.noleftmargin ? '0' : '20px')};
`;

const ToolbarGroup = styled(PFToolbarGroup)`
  &&& {
    margin: 0;
  }
`;

const ColumnLeft = styled.div`
  display: flex;
  flex-basis: 100%;
  justify-content: flex-start;
  align-items: center;
  padding: 10px 0 8px 0;

  @media screen and (min-width: 980px) {
    flex-basis: 50%;
  }
`;

const ColumnRight = styled(ColumnLeft)`
  margin-left: 60px;
  padding: 8px 0 10px 0;

  @media screen and (min-width: 980px) {
    margin-left: 0;
    padding: 10px 0 8px 0;
  }
`;

const AdditionalControlsWrapper = styled.div`
  display: flex;
  flex-grow: 1;
  justify-content: flex-end;
`;

class DataListToolbar extends React.Component {
  render () {
    const {
      columns,
      showSelectAll,
      isAllSelected,
      isCompact,
      noLeftMargin,
      onSort,
      onSearch,
      onCompact,
      onExpand,
      onSelectAll,
      sortOrder,
      sortedColumnKey,
      additionalControls,
    } = this.props;

    const showExpandCollapse = (onCompact && onExpand);
    return (
      <I18n>
        {({ i18n }) => (
          <AWXToolbar>
            <Toolbar noleftmargin={noLeftMargin}>
              { showSelectAll && (
                <Fragment>
                  <ColumnLeft>
                    <ToolbarItem>
                      <Checkbox
                        checked={isAllSelected}
                        onChange={onSelectAll}
                        aria-label={i18n._(t`Select all`)}
                        id="select-all"
                      />
                    </ToolbarItem>
                    <VerticalSeparator />
                    <ToolbarItem css="flex-grow: 1;">
                      <Search
                        columns={columns}
                        onSearch={onSearch}
                        sortedColumnKey={sortedColumnKey}
                      />
                    </ToolbarItem>
                    <VerticalSeparator />
                  </ColumnLeft>
                  <ColumnRight>
                    <ToolbarItem>
                      <Sort
                        columns={columns}
                        onSort={onSort}
                        sortOrder={sortOrder}
                        sortedColumnKey={sortedColumnKey}
                      />
                    </ToolbarItem>
                    { (showExpandCollapse || additionalControls.length) ? (
                      <VerticalSeparator />
                    ) : null}
                    {showExpandCollapse && (
                      <Fragment>
                        <ToolbarGroup>
                          <ExpandCollapse
                            isCompact={isCompact}
                            onCompact={onCompact}
                            onExpand={onExpand}
                          />
                        </ToolbarGroup>
                        { additionalControls && (
                          <VerticalSeparator />
                        )}
                      </Fragment>
                    )}
                    <AdditionalControlsWrapper>
                      {additionalControls}
                    </AdditionalControlsWrapper>
                  </ColumnRight>
                </Fragment>
              )}
            </Toolbar>
          </AWXToolbar>

        )}
      </I18n>
    );
  }
}

DataListToolbar.propTypes = {
  columns: PropTypes.arrayOf(PropTypes.object).isRequired,
  showSelectAll: PropTypes.bool,
  isAllSelected: PropTypes.bool,
  isCompact: PropTypes.bool,
  noLeftMargin: PropTypes.bool,
  onCompact: PropTypes.func,
  onExpand: PropTypes.func,
  onSearch: PropTypes.func,
  onSelectAll: PropTypes.func,
  onSort: PropTypes.func,
  sortOrder: PropTypes.string,
  sortedColumnKey: PropTypes.string,
  additionalControls: PropTypes.arrayOf(PropTypes.node),
};

DataListToolbar.defaultProps = {
  showSelectAll: false,
  isAllSelected: false,
  isCompact: false,
  noLeftMargin: false,
  onCompact: null,
  onExpand: null,
  onSearch: null,
  onSelectAll: null,
  onSort: null,
  sortOrder: 'ascending',
  sortedColumnKey: 'name',
  additionalControls: [],
};

export default DataListToolbar;
