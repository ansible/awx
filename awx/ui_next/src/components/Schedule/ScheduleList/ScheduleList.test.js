import React from 'react';
import { act } from 'react-dom/test-utils';
import { SchedulesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ScheduleList from './ScheduleList';
import mockSchedules from '../data.schedules.json';

jest.mock('../../../api');

describe('ScheduleList', () => {
  let wrapper;
  let loadSchedules;
  let loadScheduleOptions;

  describe('read call successful', () => {
    beforeEach(async () => {
      SchedulesAPI.destroy = jest.fn();
      SchedulesAPI.update.mockResolvedValue({
        data: mockSchedules.results[0],
      });
      SchedulesAPI.read.mockResolvedValue({ data: mockSchedules });
      SchedulesAPI.readOptions.mockResolvedValue({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      });
      loadSchedules = jest.fn();
      loadSchedules.mockResolvedValue({ data: mockSchedules });
      loadScheduleOptions = jest.fn();
      loadScheduleOptions.mockResolvedValue({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      });
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleList
            loadSchedules={loadSchedules}
            loadScheduleOptions={loadScheduleOptions}
            resource={{ type: 'job_template', inventory: 1 }}
            launchConfig={{ survey_enabled: false }}
            surveyConfig={{}}
          />
        );
      });
      wrapper.update();
    });

    test('should fetch schedules from api and render the list', () => {
      expect(loadSchedules).toHaveBeenCalled();
      expect(wrapper.find('ScheduleListItem').length).toBe(5);
    });

    test('should show add button', () => {
      expect(wrapper.find('ToolbarAddButton').length).toBe(1);
    });

    test('should check and uncheck the row item', async () => {
      expect(
        wrapper.find('.pf-c-table__check').first().find('input').props().checked
      ).toBe(false);
      await act(async () => {
        wrapper
          .find('.pf-c-table__check')
          .first()
          .find('input')
          .invoke('onChange')(true);
      });
      wrapper.update();
      expect(
        wrapper.find('.pf-c-table__check').first().find('input').props().checked
      ).toBe(true);
      await act(async () => {
        wrapper
          .find('.pf-c-table__check')
          .first()
          .find('input')
          .invoke('onChange')(false);
      });
      wrapper.update();
      expect(
        wrapper.find('.pf-c-table__check').first().find('input').props().checked
      ).toBe(false);
    });

    test('should check all row items when select all is checked', async () => {
      expect(wrapper.find('.pf-c-table__check input')).toHaveLength(5);
      wrapper.find('.pf-c-table__check input').forEach((el) => {
        expect(el.props().checked).toBe(false);
      });
      await act(async () => {
        wrapper.find('Checkbox#select-all').invoke('onChange')(true);
      });
      wrapper.update();
      wrapper.find('.pf-c-table__check input').forEach((el) => {
        expect(el.props().checked).toBe(true);
      });
      await act(async () => {
        wrapper.find('Checkbox#select-all').invoke('onChange')(false);
      });
      wrapper.update();
      wrapper.find('.pf-c-table__check input').forEach((el) => {
        expect(el.props().checked).toBe(false);
      });
    });

    test('should call api delete schedules for each selected schedule', async () => {
      await act(async () => {
        wrapper.find('.pf-c-table__check input').at(3).invoke('onChange')();
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
      });
      wrapper.update();
      expect(SchedulesAPI.destroy).toHaveBeenCalledTimes(1);
    });

    test('should show error modal when schedule is not successfully deleted from api', async () => {
      SchedulesAPI.destroy.mockImplementationOnce(() =>
        Promise.reject(new Error())
      );
      expect(wrapper.find('Modal').length).toBe(0);
      await act(async () => {
        wrapper.find('.pf-c-table__check input').at(2).invoke('onChange')();
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
      });
      wrapper.update();
      expect(wrapper.find('Modal').length).toBe(1);
      await act(async () => {
        wrapper.find('ModalBoxCloseButton').invoke('onClose')();
      });
      wrapper.update();
      expect(wrapper.find('Modal').length).toBe(0);
    });

    test('should call api update schedules when toggle clicked', async () => {
      await act(async () => {
        wrapper
          .find('Switch[id="schedule-5-toggle"]')
          .first()
          .invoke('onChange')();
      });
      wrapper.update();
      expect(SchedulesAPI.update).toHaveBeenCalledTimes(1);
    });

    test('should show error modal when schedule is not successfully updated on toggle', async () => {
      SchedulesAPI.update.mockImplementationOnce(() =>
        Promise.reject(new Error())
      );
      expect(wrapper.find('Modal').length).toBe(0);
      await act(async () => {
        wrapper
          .find('Switch[id="schedule-1-toggle"]')
          .first()
          .invoke('onChange')();
      });
      wrapper.update();
      expect(wrapper.find('Modal').length).toBe(1);
      await act(async () => {
        wrapper.find('ModalBoxCloseButton').invoke('onClose')();
      });
      wrapper.update();
      expect(wrapper.find('Modal').length).toBe(0);
    });
  });

  describe('hidden add button', () => {
    beforeEach(async () => {
      SchedulesAPI.destroy = jest.fn();
      SchedulesAPI.update.mockResolvedValue({
        data: mockSchedules.results[0],
      });
      SchedulesAPI.read.mockResolvedValue({ data: mockSchedules });
      SchedulesAPI.readOptions.mockResolvedValue({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      });
      loadSchedules = jest.fn();
      loadSchedules.mockResolvedValue({ data: mockSchedules });
      loadScheduleOptions = jest.fn();
      loadScheduleOptions.mockResolvedValue({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      });
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleList
            loadSchedules={loadSchedules}
            loadScheduleOptions={loadScheduleOptions}
            resource={{ type: 'job_template', inventory: 1 }}
            launchConfig={{ survey_enabled: false }}
            surveyConfig={{}}
          />
        );
      });
      wrapper.update();
    });
    test('should hide add button when flag is passed', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleList
            loadSchedules={loadSchedules}
            loadScheduleOptions={loadScheduleOptions}
            hideAddButton
          />
        );
      });
      wrapper.update();
      expect(wrapper.find('ToolbarAddButton').length).toBe(0);
    });
    test('should show missing resource icon and disabled toggle', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleList
            loadSchedules={loadSchedules}
            loadScheduleOptions={loadScheduleOptions}
            hideAddButton
            resource={{ type: 'job_template', inventory: 1 }}
            launchConfig={{ survey_enabled: true }}
            surveyConfig={{ spec: [{ required: true, default: null }] }}
          />
        );
      });
      wrapper.update();
      expect(
        wrapper.find('ScheduleListItem').at(4).prop('isMissingSurvey')
      ).toBe('This schedule is missing required survey values');
      expect(wrapper.find('ExclamationTriangleIcon').length).toBe(5);
      expect(wrapper.find('Switch#schedule-5-toggle').prop('isDisabled')).toBe(
        true
      );
    });
    test('should show missing resource icon and disabled toggle', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleList
            loadSchedules={loadSchedules}
            loadScheduleOptions={loadScheduleOptions}
            hideAddButton
            resource={{ type: 'job_template' }}
            launchConfig={{
              survey_enabled: true,
              inventory_needed_to_start: true,
            }}
            surveyConfig={{ spec: [] }}
          />
        );
      });
      wrapper.update();

      expect(
        wrapper.find('ScheduleListItem').at(3).prop('isMissingInventory')
      ).toBe('This schedule is missing an Inventory');
      expect(wrapper.find('ExclamationTriangleIcon').length).toBe(4);
      expect(wrapper.find('Switch#schedule-3-toggle').prop('isDisabled')).toBe(
        true
      );
    });
  });

  describe('read call unsuccessful', () => {
    beforeEach(async () => {
      SchedulesAPI.destroy = jest.fn();
      SchedulesAPI.update.mockResolvedValue({
        data: mockSchedules.results[0],
      });
      SchedulesAPI.read.mockResolvedValue({ data: mockSchedules });
      SchedulesAPI.readOptions.mockResolvedValue({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      });
      loadSchedules = jest.fn();
      loadSchedules.mockResolvedValue({ data: mockSchedules });
      loadScheduleOptions = jest.fn();
      loadScheduleOptions.mockResolvedValue({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      });
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleList
            loadSchedules={loadSchedules}
            loadScheduleOptions={loadScheduleOptions}
            resource={{ type: 'job_template', inventory: 1 }}
            launchConfig={{ survey_enabled: false }}
            surveyConfig={{}}
          />
        );
      });
      wrapper.update();
    });
    test('should show content error when read call unsuccessful', async () => {
      SchedulesAPI.read.mockRejectedValue(new Error());
      loadSchedules.mockRejectedValue(new Error());
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleList
            loadSchedules={loadSchedules}
            loadScheduleOptions={loadScheduleOptions}
          />
        );
      });
      wrapper.update();
      expect(wrapper.find('ContentError').length).toBe(1);
    });
  });
});
