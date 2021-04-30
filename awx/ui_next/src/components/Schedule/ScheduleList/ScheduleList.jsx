import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import { SchedulesAPI } from '../../../api';
import AlertModal from '../../AlertModal';
import ErrorDetail from '../../ErrorDetail';
import PaginatedTable, { HeaderRow, HeaderCell } from '../../PaginatedTable';
import DataListToolbar from '../../DataListToolbar';
import { ToolbarAddButton, ToolbarDeleteButton } from '../../PaginatedDataList';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import ScheduleListItem from './ScheduleListItem';

const QS_CONFIG = getQSConfig('schedule', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function ScheduleList({
  loadSchedules,
  loadScheduleOptions,
  hideAddButton,
  resource,
  launchConfig,
  surveyConfig,
}) {
  const [selected, setSelected] = useState([]);

  const location = useLocation();

  const {
    result: {
      schedules,
      itemCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
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
        relatedSearchableKeys: (
          scheduleActions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          scheduleActions.data.actions?.GET || {}
        ).filter(key => scheduleActions.data.actions?.GET[key].filterable),
      };
    }, [location.search, loadSchedules, loadScheduleOptions]),
    {
      schedules: [],
      itemCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
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
  const isTemplate =
    resource?.type === 'workflow_job_template' ||
    resource?.type === 'job_template';

  const missingRequiredInventory = schedule => {
    if (
      !launchConfig.inventory_needed_to_start ||
      schedule?.summary_fields?.inventory?.id
    ) {
      return null;
    }
    return t`This schedule is missing an Inventory`;
  };

  const hasMissingSurveyValue = schedule => {
    let missingValues;
    if (launchConfig.survey_enabled) {
      surveyConfig.spec.forEach(question => {
        const hasDefaultValue = Boolean(question.default);
        if (question.required && !hasDefaultValue) {
          const extraDataKeys = Object.keys(schedule?.extra_data);

          const hasMatchingKey = extraDataKeys.includes(question.variable);
          Object.values(schedule?.extra_data).forEach(value => {
            if (!value || !hasMatchingKey) {
              missingValues = true;
            } else {
              missingValues = false;
            }
          });
          if (!Object.values(schedule.extra_data).length) {
            missingValues = true;
          }
        }
      });
    }
    return missingValues && t`This schedule is missing required survey values`;
  };

  return (
    <>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading || isDeleteLoading}
        items={schedules}
        itemCount={itemCount}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell>{t`Type`}</HeaderCell>
            <HeaderCell sortKey="next_run">{t`Next Run`}</HeaderCell>
            <HeaderCell>{t`Actions`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(item, index) => (
          <ScheduleListItem
            isSelected={selected.some(row => row.id === item.id)}
            key={item.id}
            onSelect={() => handleSelect(item)}
            schedule={item}
            rowIndex={index}
            isMissingInventory={isTemplate && missingRequiredInventory(item)}
            isMissingSurvey={isTemplate && hasMissingSurveyValue(item)}
          />
        )}
        toolbarSearchColumns={[
          {
            name: t`Name`,
            key: 'name__icontains',
            isDefault: true,
          },
          {
            name: t`Description`,
            key: 'description__icontains',
          },
          {
            name: t`Created By (Username)`,
            key: 'created_by__username__icontains',
          },
          {
            name: t`Modified By (Username)`,
            key: 'modified_by__username__icontains',
          },
        ]}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
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
                pluralizedItemName={t`Schedules`}
              />,
            ]}
          />
        )}
      />
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="danger"
          title={t`Error!`}
          onClose={clearDeletionError}
        >
          {t`Failed to delete one or more schedules.`}
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

export default ScheduleList;
