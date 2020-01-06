import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CredentialsAPI } from '@api';
import { Card, PageSection } from '@patternfly/react-core';
import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';
import DataListToolbar from '@components/DataListToolbar';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';
import { CredentialListItem } from '.';

const QS_CONFIG = getQSConfig('credential', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function CredentialList({ i18n }) {
  const [actions, setActions] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [credentialCount, setCredentialCount] = useState(0);
  const [credentials, setCredentials] = useState([]);
  const [deletionError, setDeletionError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [selected, setSelected] = useState([]);

  const location = useLocation();

  const loadCredentials = async ({ search }) => {
    const params = parseQueryString(QS_CONFIG, search);
    setContentError(null);
    setHasContentLoading(true);
    try {
      const [
        {
          data: { count, results },
        },
        {
          data: { actions: optionActions },
        },
      ] = await Promise.all([
        CredentialsAPI.read(params),
        loadCredentialActions(),
      ]);

      setCredentials(results);
      setCredentialCount(count);
      setActions(optionActions);
    } catch (error) {
      setContentError(error);
    } finally {
      setHasContentLoading(false);
    }
  };

  useEffect(() => {
    loadCredentials(location);
  }, [location]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadCredentialActions = () => {
    if (actions) {
      return Promise.resolve({ data: { actions } });
    }
    return CredentialsAPI.readOptions();
  };

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...credentials] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

  const handleDelete = async () => {
    setHasContentLoading(true);

    try {
      await Promise.all(
        selected.map(credential => CredentialsAPI.destroy(credential.id))
      );
    } catch (error) {
      setDeletionError(error);
    }

    const params = parseQueryString(QS_CONFIG, location.search);
    try {
      const {
        data: { count, results },
      } = await CredentialsAPI.read(params);

      setCredentials(results);
      setCredentialCount(count);
      setSelected([]);
    } catch (error) {
      setContentError(error);
    }

    setHasContentLoading(false);
  };

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const isAllSelected =
    selected.length > 0 && selected.length === credentials.length;

  return (
    <PageSection>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={hasContentLoading}
          items={credentials}
          itemCount={credentialCount}
          qsConfig={QS_CONFIG}
          onRowClick={handleSelect}
          renderItem={item => (
            <CredentialListItem
              key={item.id}
              credential={item}
              detailUrl={`/credentials/${item.id}/details`}
              isSelected={selected.some(row => row.id === item.id)}
              onSelect={() => handleSelect(item)}
            />
          )}
          renderToolbar={props => (
            <DataListToolbar
              {...props}
              showSelectAll
              isAllSelected={isAllSelected}
              onSelectAll={handleSelectAll}
              qsConfig={QS_CONFIG}
              additionalControls={[
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={i18n._(t`Credentials`)}
                />,
                canAdd && (
                  <ToolbarAddButton key="add" linkTo="/credentials/add" />
                ),
              ]}
            />
          )}
        />
      </Card>
      <AlertModal
        isOpen={deletionError}
        variant="danger"
        title={i18n._(t`Error!`)}
        onClose={() => setDeletionError(null)}
      >
        {i18n._(t`Failed to delete one or more credentials.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </PageSection>
  );
}

export default withI18n()(CredentialList);
