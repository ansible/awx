import React, { Fragment, useState, useEffect, useCallback } from 'react';
import { Link, useHistory, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import {
  Button,
  Chip,
  TextList,
  TextListItem,
  TextListItemVariants,
  TextListVariants,
  Label,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';

import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import ChipGroup from '../../../components/ChipGroup';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import CredentialChip from '../../../components/CredentialChip';
import {
  Detail,
  DetailList,
  DeletedDetail,
  UserDateDetail,
} from '../../../components/DetailList';
import DeleteButton from '../../../components/DeleteButton';
import ErrorDetail from '../../../components/ErrorDetail';
import LaunchButton from '../../../components/LaunchButton';
import { VariablesDetail } from '../../../components/CodeMirrorInput';
import { JobTemplatesAPI } from '../../../api';
import useRequest, { useDismissableError } from '../../../util/useRequest';

function NotificationTemplateDetail({ i18n, template }) {
  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail
          label={i18n._(t`Name`)}
          value={template.name}
          dataCy="nt-detail-name"
        />
      </DetailList>
    </CardBody>
  );
}

export default withI18n()(NotificationTemplateDetail);
