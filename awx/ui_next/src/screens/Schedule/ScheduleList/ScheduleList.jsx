import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { SchedulesAPI } from '@api';
import { Card, PageSection } from '@patternfly/react-core';
import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';
import DataListToolbar from '@components/DataListToolbar';
import PaginatedDataList, {
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';
import { ScheduleListItem } from '.';

const QS_CONFIG = getQSConfig('schedule', {
  page: 1,
  page_size: 20,
  order_by: 'unified_job_template__polymorphic_ctype__model',
});

function ScheduleList({ i18n }) {
  const [contentError, setContentError] = useState(null);
  const [scheduleCount, setScheduleCount] = useState(0);
  const [schedules, setSchedules] = useState([]);
  const [deletionError, setDeletionError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [selected, setSelected] = useState([]);
  const [toggleError, setToggleError] = useState(null);
  const [toggleLoading, setToggleLoading] = useState(null);

  const location = useLocation();

  const loadSchedules = async ({ search }) => {
    const params = parseQueryString(QS_CONFIG, search);
    setContentError(null);
    setHasContentLoading(true);
    try {
      const {
        data: { count, results },
      } = await SchedulesAPI.read(params);

      setSchedules(results);
      setScheduleCount(count);
    } catch (error) {
      setContentError(error);
    } finally {
      setHasContentLoading(false);
    }
  };

  useEffect(() => {
    loadSchedules(location);
  }, [location]); // eslint-disable-line react-hooks/exhaustive-deps

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
    setHasContentLoading(true);

    try {
      await Promise.all(
        selected.map(schedule => SchedulesAPI.destroy(schedule.id))
      );
    } catch (error) {
      setDeletionError(error);
    }

    const params = parseQueryString(QS_CONFIG, location.search);
    try {
      const {
        data: { count, results },
      } = await SchedulesAPI.read(params);

      setSchedules(results);
      setScheduleCount(count);
      setSelected([]);
    } catch (error) {
      setContentError(error);
    }

    setHasContentLoading(false);
  };

  const handleScheduleToggle = async scheduleToToggle => {
    setToggleLoading(scheduleToToggle.id);
    try {
      const { data: updatedSchedule } = await SchedulesAPI.update(
        scheduleToToggle.id,
        {
          enabled: !scheduleToToggle.enabled,
        }
      );
      setSchedules(
        schedules.map(schedule =>
          schedule.id === updatedSchedule.id ? updatedSchedule : schedule
        )
      );
    } catch (err) {
      setToggleError(err);
    } finally {
      setToggleLoading(null);
    }
  };

  const isAllSelected =
    selected.length > 0 && selected.length === schedules.length;

  return (
    <PageSection>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={hasContentLoading}
          items={schedules}
          itemCount={scheduleCount}
          qsConfig={QS_CONFIG}
          onRowClick={handleSelect}
          renderItem={item => (
            <ScheduleListItem
              isSelected={selected.some(row => row.id === item.id)}
              key={item.id}
              onSelect={() => handleSelect(item)}
              onToggleSchedule={handleScheduleToggle}
              schedule={item}
              toggleLoading={toggleLoading === item.id}
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
      </Card>
      {toggleError && !toggleLoading && (
        <AlertModal
          variant="danger"
          title={i18n._(t`Error!`)}
          isOpen={toggleError && !toggleLoading}
          onClose={() => setToggleError(null)}
        >
          {i18n._(t`Failed to toggle schedule.`)}
          <ErrorDetail error={toggleError} />
        </AlertModal>
      )}
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="danger"
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete one or more schedules.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </PageSection>
  );
}

export default withI18n()(ScheduleList);
