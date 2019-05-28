import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  ActionGroup as PFActionGroup,
  Toolbar,
  ToolbarGroup,
  Button
} from '@patternfly/react-core';
import styled from 'styled-components';

const ActionGroup = styled(PFActionGroup)`
    display: flex;
    flex-direction: row;
    justify-content: flex-end;
    --pf-c-form__group--m-action--MarginTop: 0;
`;

const FormActionGroup = ({ onSubmit, submitDisabled, onCancel, i18n }) => (
  <ActionGroup>
    <Toolbar>
      <ToolbarGroup css="margin-right: 20px">
        <Button aria-label={i18n._(t`Save`)} variant="primary" type="submit" onClick={onSubmit} isDisabled={submitDisabled}>{i18n._(t`Save`)}</Button>
      </ToolbarGroup>
      <ToolbarGroup>
        <Button aria-label={i18n._(t`Cancel`)} variant="secondary" type="button" onClick={onCancel}>{i18n._(t`Cancel`)}</Button>
      </ToolbarGroup>
    </Toolbar>
  </ActionGroup>
);

FormActionGroup.propTypes = {
  onCancel: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  submitDisabled: PropTypes.bool,
};

FormActionGroup.defaultProps = {
  submitDisabled: false,
};

export default withI18n()(FormActionGroup);
