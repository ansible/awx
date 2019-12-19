import React, { useState } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import {
  Card as _Card,
  CardHeader,
  PageSection,
  Tooltip,
} from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import UserForm from '../shared/UserForm';
import { UsersAPI } from '@api';

const Card = styled(_Card)`
  --pf-c-card--child--PaddingLeft: 0;
  --pf-c-card--child--PaddingRight: 0;
`;

function UserAdd({ history, i18n }) {
  const [formSubmitError, setFormSubmitError] = useState(null);

  const handleSubmit = async values => {
    setFormSubmitError(null);
    try {
      const {
        data: { id },
      } = await UsersAPI.create(values);
      history.push(`/users/${id}/details`);
    } catch (error) {
      setFormSubmitError(error);
    }
  };

  const handleCancel = () => {
    history.push(`/users`);
  };

  return (
    <PageSection>
      <Card>
        <CardHeader className="at-u-textRight">
          <Tooltip content={i18n._(t`Close`)} position="top">
            <CardCloseButton onClick={handleCancel} />
          </Tooltip>
        </CardHeader>
        <CardBody>
          <UserForm handleCancel={handleCancel} handleSubmit={handleSubmit} />
        </CardBody>
        {formSubmitError ? (
          <div className="formSubmitError">formSubmitError</div>
        ) : (
          ''
        )}
      </Card>
    </PageSection>
  );
}

export default withI18n()(withRouter(UserAdd));
