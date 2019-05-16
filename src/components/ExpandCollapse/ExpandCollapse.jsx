import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  ToolbarItem
} from '@patternfly/react-core';
import {
  BarsIcon,
  EqualsIcon,
} from '@patternfly/react-icons';

const ToolbarActiveStyle = {
  backgroundColor: '#007bba',
  color: 'white',
  padding: '0 5px',
};

class ExpandCollapse extends React.Component {
  render () {
    const {
      onCompact,
      onExpand,
      isCompact,
      i18n
    } = this.props;

    return (
      <Fragment>
        <ToolbarItem>
          <Button
            variant="plain"
            aria-label={i18n._(t`Collapse`)}
            onClick={onCompact}
            style={isCompact ? ToolbarActiveStyle : null}
          >
            <BarsIcon />
          </Button>
        </ToolbarItem>
        <ToolbarItem>
          <Button
            variant="plain"
            aria-label={i18n._(t`Expand`)}
            onClick={onExpand}
            style={!isCompact ? ToolbarActiveStyle : null}
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
  isCompact: PropTypes.bool.isRequired
};

ExpandCollapse.defaultProps = {};

export default withI18n()(ExpandCollapse);
