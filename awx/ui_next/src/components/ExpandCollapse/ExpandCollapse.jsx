import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button as PFButton,
  ToolbarItem as PFToolbarItem,
} from '@patternfly/react-core';
import { BarsIcon, EqualsIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

const Button = styled(PFButton)`
  padding: 0;
  margin: 0;
  height: 30px;
  width: 30px;
  ${props =>
    props.isActive
      ? `
      background-color: #007bba;
      --pf-c-button--m-plain--active--Color: white;
      --pf-c-button--m-plain--focus--Color: white;`
      : null};
`;

const ToolbarItem = styled(PFToolbarItem)`
  & :not(:last-child) {
    margin-right: 20px;
  }
`;

// TODO: Recommend renaming this component to avoid confusion
// with ExpandingContainer
class ExpandCollapse extends React.Component {
  render() {
    const { isCompact, onCompact, onExpand, i18n } = this.props;

    return (
      <Fragment>
        <ToolbarItem>
          <Button
            variant="plain"
            aria-label={i18n._(t`Collapse`)}
            onClick={onCompact}
            isActive={isCompact}
          >
            <BarsIcon />
          </Button>
        </ToolbarItem>
        <ToolbarItem>
          <Button
            variant="plain"
            aria-label={i18n._(t`Expand`)}
            onClick={onExpand}
            isActive={!isCompact}
          >
            <EqualsIcon />
          </Button>
        </ToolbarItem>
      </Fragment>
    );
  }
}

ExpandCollapse.propTypes = {
  onCompact: PropTypes.func.isRequired,
  onExpand: PropTypes.func.isRequired,
  isCompact: PropTypes.bool,
};

ExpandCollapse.defaultProps = {
  isCompact: true,
};

export default withI18n()(ExpandCollapse);
