import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Checkbox,
  Level,
  LevelItem,
  Toolbar,
  ToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';

import ExpandCollapse from '../ExpandCollapse';
import Search from '../Search';
import Sort from '../Sort';
import VerticalSeparator from '../VerticalSeparator';

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
          <div className="awx-toolbar">
            <Level>
              <LevelItem style={{ display: 'flex', flexBasis: '700px' }}>
                <Toolbar style={{ marginLeft: noLeftMargin ? '0px' : '20px', flexGrow: '1' }}>
                  { showSelectAll && (
                    <ToolbarGroup>
                      <ToolbarItem>
                        <Checkbox
                          checked={isAllSelected}
                          onChange={onSelectAll}
                          aria-label={i18n._(t`Select all`)}
                          id="select-all"
                        />
                      </ToolbarItem>
                      <VerticalSeparator />
                    </ToolbarGroup>
                  )}
                  <ToolbarGroup style={{ flexGrow: '1' }}>
                    <ToolbarItem style={{ flexGrow: '1' }}>
                      <Search
                        columns={columns}
                        onSearch={onSearch}
                        sortedColumnKey={sortedColumnKey}
                      />
                    </ToolbarItem>
                    <VerticalSeparator />
                  </ToolbarGroup>
                  <ToolbarGroup
                    className="sortDropdownGroup"
                  >
                    <ToolbarItem>
                      <Sort
                        columns={columns}
                        onSort={onSort}
                        sortOrder={sortOrder}
                        sortedColumnKey={sortedColumnKey}
                      />
                    </ToolbarItem>
                  </ToolbarGroup>
                  {showExpandCollapse && (
                    <Fragment>
                      <VerticalSeparator />
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
                </Toolbar>
              </LevelItem>
              <LevelItem>
                {additionalControls}
              </LevelItem>
            </Level>
          </div>
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
