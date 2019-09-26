import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
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

import { QSConfig } from '@types';

const AWXToolbar = styled.div`
  --awx-toolbar--BackgroundColor: var(--pf-global--BackgroundColor--light-100);
  --awx-toolbar--BorderColor: #ebebeb;
  --awx-toolbar--BorderWidth: var(--pf-global--BorderWidth--sm);

  --pf-global--target-size--MinHeight: 0;
  --pf-global--target-size--MinWidth: 0;
  --pf-global--FontSize--md: 14px;

  border-bottom: var(--awx-toolbar--BorderWidth) solid
    var(--awx-toolbar--BorderColor);
  background-color: var(--awx-toolbar--BackgroundColor);
  display: flex;
  min-height: 70px;
  flex-grow: 1;
`;

const Toolbar = styled(PFToolbar)`
  flex-grow: 1;
  margin-left: 20px;
  margin-right: 20px;
`;

const ToolbarGroup = styled(PFToolbarGroup)`
  &&& {
    margin: 0;
  }
`;

const ColumnLeft = styled.div`
  display: flex;
  flex-basis: ${props => (props.fillWidth ? 'auto' : '100%')};
  flex-grow: ${props => (props.fillWidth ? '1' : '0')};
  justify-content: flex-start;
  align-items: center;
  padding: 10px 0 8px 0;

  @media screen and (min-width: 980px) {
    flex-basis: ${props => (props.fillWidth ? 'auto' : '50%')};
  }
`;

const ColumnRight = styled.div`
  display: flex;
  flex-basis: ${props => (props.fillWidth ? 'auto' : '100%')};
  flex-grow: 0;
  justify-content: flex-start;
  align-items: center;
  padding: 8px 0 10px 0;

  @media screen and (min-width: 980px) {
    flex-basis: ${props => (props.fillWidth ? 'auto' : '50%')};
  }
`;

const AdditionalControlsWrapper = styled.div`
  display: flex;
  flex-grow: 1;
  justify-content: flex-end;
  align-items: center;

  & > :not(:first-child) {
    margin-left: 20px;
  }
`;

class DataListToolbar extends React.Component {
  render() {
    const {
      columns,
      showSelectAll,
      isAllSelected,
      isCompact,
      fillWidth,
      onSort,
      onSearch,
      onCompact,
      onExpand,
      onSelectAll,
      sortOrder,
      sortedColumnKey,
      additionalControls,
      i18n,
      qsConfig,
    } = this.props;

    const showExpandCollapse = onCompact && onExpand;
    return (
      <AWXToolbar>
        <Toolbar css={fillWidth ? 'margin-right: 0; margin-left: 0' : ''}>
          <ColumnLeft fillWidth={fillWidth}>
            {showSelectAll && (
              <Fragment>
                <ToolbarItem>
                  <Checkbox
                    isChecked={isAllSelected}
                    onChange={onSelectAll}
                    aria-label={i18n._(t`Select all`)}
                    id="select-all"
                  />
                </ToolbarItem>
                <VerticalSeparator />
              </Fragment>
            )}
            <ToolbarItem css="flex-grow: 1;">
              <Search
                qsConfig={qsConfig}
                columns={columns}
                onSearch={onSearch}
                sortedColumnKey={sortedColumnKey}
              />
            </ToolbarItem>
            <VerticalSeparator />
          </ColumnLeft>
          <ColumnRight fillWidth={fillWidth}>
            <ToolbarItem>
              <Sort
                columns={columns}
                onSort={onSort}
                sortOrder={sortOrder}
                sortedColumnKey={sortedColumnKey}
              />
            </ToolbarItem>
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
                {additionalControls && <VerticalSeparator />}
              </Fragment>
            )}
            <AdditionalControlsWrapper>
              {additionalControls}
            </AdditionalControlsWrapper>
          </ColumnRight>
        </Toolbar>
      </AWXToolbar>
    );
  }
}

DataListToolbar.propTypes = {
  qsConfig: QSConfig.isRequired,
  columns: PropTypes.arrayOf(PropTypes.object).isRequired,
  showSelectAll: PropTypes.bool,
  isAllSelected: PropTypes.bool,
  isCompact: PropTypes.bool,
  fillWidth: PropTypes.bool,
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
  fillWidth: false,
  onCompact: null,
  onExpand: null,
  onSearch: null,
  onSelectAll: null,
  onSort: null,
  sortOrder: 'ascending',
  sortedColumnKey: 'name',
  additionalControls: [],
};

export default withI18n()(DataListToolbar);
