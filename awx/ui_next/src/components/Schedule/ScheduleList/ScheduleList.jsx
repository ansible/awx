import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { SchedulesAPI } from '@api';
import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';
import DataListToolbar from '@components/DataListToolbar';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import useRequest, { useDeleteItems } from '@util/useRequest';
import { getQSConfig, parseQueryString } from '@util/qs';
import ScheduleListItem from './ScheduleListItem';

const QS_CONFIG = getQSConfig('schedule', {
  page: 1,
  page_size: 20,
  order_by: 'unified_job_template__polymorphic_ctype__model',
});

function ScheduleList({
  i18n,
  loadSchedules,
  loadScheduleOptions,
  hideAddButton,
}) {
  const [selected, setSelected] = useState([]);

  const location = useLocation();

  const {
    result: { schedules, itemCount, actions },
    error: contentError,
    isLoading,
    request: fetchSchedules,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [
        {
          data: { count, results },
        },
        scheduleActions,
      ] = await Promise.all([loadSchedules(params), loadScheduleOptions()]);
      return {
        schedules: results,
        itemCount: count,
        actions: scheduleActions.data.actions,
      };
    }, [location, loadSchedules, loadScheduleOptions]),
    {
      schedules: [],
      itemCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchSchedules();
  }, [fetchSchedules]);

  const isAllSelected =
    selected.length === schedules.length && selected.length > 0;

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteJobs,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(selected.map(({ id }) => SchedulesAPI.destroy(id)));
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchSchedules,
    }
  );

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...schedules] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

  const handleDelete = async () => {
    await deleteJobs();
    setSelected([]);
  };

  const canAdd =
    actions &&
    Object.prototype.hasOwnProperty.call(actions, 'POST') &&
    !hideAddButton;

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading || isDeleteLoading}
        items={schedules}
        itemCount={itemCount}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        renderItem={item => (
          <ScheduleListItem
            isSelected={selected.some(row => row.id === item.id)}
            key={item.id}
            onSelect={() => handleSelect(item)}
            schedule={item}
          />
        )}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
            isDefault: true,
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
          },
          {
            name: i18n._(t`Next Run`),
            key: 'next_run',
          },
          {
            name: i18n._(t`Type`),
            key: 'unified_job_template__polymorphic_ctype__model',
          },
        ]}
        renderToolbar={props => (
          <DataListToolbar
            {...props}
            showSelectAll
            isAllSelected={isAllSelected}
            onSelectAll={handleSelectAll}
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [
                    <ToolbarAddButton
                      key="add"
                      linkTo={`${location.pathname}/add`}
                    />,
                  ]
                : []),
              <ToolbarDeleteButton
                key="delete"
                onDelete={handleDelete}
                itemsToDelete={selected}
                pluralizedItemName={i18n._(t`Schedules`)}
              />,
            ]}
          />
        )}
      />
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="danger"
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more schedules.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
}

ScheduleList.propTypes = {
  hideAddButton: bool,
  loadSchedules: func.isRequired,
  loadScheduleOptions: func.isRequired,
};
ScheduleList.defaultProps = {
  hideAddButton: false,
};

export default withI18n()(ScheduleList);
