import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Checkbox,
  Level,
  LevelItem,
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

  border-bottom: var(--awx-toolbar--BorderWidth) solid var(--awx-toolbar--BorderColor);
  background-color: var(--awx-toolbar--BackgroundColor);
  display: flex;
  min-height: 70px;
  padding-top: 5px;

  --pf-global--target-size--MinHeight: 0px;
  --pf-global--target-size--MinWidth: 0px;
  --pf-global--FontSize--md: 14px;
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
          <AWXToolbar className="awx-toolbar">
            <Level css="flex-grow: 1;">
              <LevelItem css="display: flex; flex-basis: 700px">
                <Toolbar noleftmargin={noLeftMargin}>
                  { showSelectAll && (
                    <ToolbarGroup css="margin: 0;">
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
                  <ToolbarGroup css="margin: 0; flex-grow: 1;">
                    <ToolbarItem css="flex-grow: 1;">
                      <Search
                        columns={columns}
                        onSearch={onSearch}
                        sortedColumnKey={sortedColumnKey}
                      />
                    </ToolbarItem>
                    <VerticalSeparator />
                  </ToolbarGroup>
                  <ToolbarGroup>
                    <ToolbarItem>
                      <Sort
                        columns={columns}
                        onSort={onSort}
                        sortOrder={sortOrder}
                        sortedColumnKey={sortedColumnKey}
                      />
                    </ToolbarItem>
                  </ToolbarGroup>
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
                </Toolbar>
              </LevelItem>
              <LevelItem css="display: flex;">
                {additionalControls}
              </LevelItem>
            </Level>
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
