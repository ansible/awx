import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Checkbox,
  Level,
  LevelItem,
  Toolbar,
  ToolbarGroup,
  ToolbarItem,
  Tooltip,
} from '@patternfly/react-core';
import {
  TrashAltIcon,
  PlusIcon,
} from '@patternfly/react-icons';
import {
  Link
} from 'react-router-dom';

import ExpandCollapse from '../ExpandCollapse';
import Search from '../Search';
import Sort from '../Sort';
import VerticalSeparator from '../VerticalSeparator';

class DataListToolbar extends React.Component {
  render () {
    const {
      addUrl,
      columns,
      disableTrashCanIcon,
      onSelectAll,
      sortedColumnKey,
      sortOrder,
      showDelete,
      showSelectAll,
      isAllSelected,
      isLookup,
      isCompact,
      onSort,
      onSearch,
      onCompact,
      onExpand,
      add,
      onOpenDeleteModal
    } = this.props;

    const showExpandCollapse = (onCompact && onExpand);
    return (
      <I18n>
        {({ i18n }) => (
          <div className="awx-toolbar">
            <Level>
              <LevelItem style={{ display: 'flex', flexBasis: '700px' }}>
                <Toolbar style={{ marginLeft: isLookup ? '0px' : '20px', flexGrow: '1' }}>
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
                  { (showExpandCollapse || showDelete || addUrl || add) && (
                    <VerticalSeparator />
                  )}
                  {showExpandCollapse && (
                    <Fragment>
                      <ToolbarGroup>
                        <ExpandCollapse
                          isCompact={isCompact}
                          onCompact={onCompact}
                          onExpand={onExpand}
                        />
                      </ToolbarGroup>
                      { (showDelete || addUrl || add) && (
                        <VerticalSeparator />
                      )}
                    </Fragment>
                  )}
                </Toolbar>
              </LevelItem>
              <LevelItem>
                { showDelete && (
                  <Tooltip
                    content={i18n._(t`Delete`)}
                    position="top"
                  >
                    <Button
                      className="awx-ToolBarBtn"
                      variant="plain"
                      aria-label={i18n._(t`Delete`)}
                      onClick={onOpenDeleteModal}
                      isDisabled={disableTrashCanIcon}
                    >
                      <TrashAltIcon className="awx-ToolBarTrashCanIcon" />
                    </Button>
                  </Tooltip>
                )}
                {addUrl && (
                  <Link to={addUrl}>
                    <Button
                      variant="primary"
                      aria-label={i18n._(t`Add`)}
                    >
                      <PlusIcon />
                    </Button>
                  </Link>
                )}
                {add && (
                  <Fragment>{add}</Fragment>
                )}
              </LevelItem>
            </Level>
          </div>
        )}
      </I18n>
    );
  }
}

DataListToolbar.propTypes = {
  addUrl: PropTypes.string,
  columns: PropTypes.arrayOf(PropTypes.object).isRequired,
  isAllSelected: PropTypes.bool,
  onSearch: PropTypes.func,
  onSelectAll: PropTypes.func,
  onSort: PropTypes.func,
  showDelete: PropTypes.bool,
  showSelectAll: PropTypes.bool,
  sortOrder: PropTypes.string,
  sortedColumnKey: PropTypes.string,
  onCompact: PropTypes.func,
  onExpand: PropTypes.func,
  isCompact: PropTypes.bool,
  add: PropTypes.node
};

DataListToolbar.defaultProps = {
  addUrl: null,
  onSearch: null,
  onSelectAll: null,
  onSort: null,
  showDelete: false,
  showSelectAll: false,
  sortOrder: 'ascending',
  sortedColumnKey: 'name',
  isAllSelected: false,
  onCompact: null,
  onExpand: null,
  isCompact: false,
  add: null
};

export default DataListToolbar;
