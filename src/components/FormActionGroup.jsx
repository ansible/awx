import React from 'react';
import PropTypes from 'prop-types';

import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  ActionGroup,
  Toolbar,
  ToolbarGroup,
  Button
} from '@patternfly/react-core';

const formActionGroupStyle = {
  display: 'flex',
  flexDirection: 'row',
  justifyContent: 'flex-end',
  marginTop: '10px'
};

const buttonGroupStyle = {
  marginRight: '20px'
};

const FormActionGroup = ({ onSubmit, submitDisabled, onCancel }) => (
  <I18n>
    {({ i18n }) => (
      <ActionGroup style={formActionGroupStyle}>
        <Toolbar>
          <ToolbarGroup style={buttonGroupStyle}>
            <Button aria-label={i18n._(t`Save`)} variant="primary" onClick={onSubmit} isDisabled={submitDisabled}>{i18n._(t`Save`)}</Button>
          </ToolbarGroup>
          <ToolbarGroup>
            <Button aria-label={i18n._(t`Cancel`)} variant="secondary" onClick={onCancel}>{i18n._(t`Cancel`)}</Button>
          </ToolbarGroup>
        </Toolbar>
      </ActionGroup>
    )}
  </I18n>
);

FormActionGroup.propTypes = {
  onCancel: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  submitDisabled: PropTypes.bool,
};

FormActionGroup.defaultProps = {
  submitDisabled: false,
};

export default FormActionGroup;
