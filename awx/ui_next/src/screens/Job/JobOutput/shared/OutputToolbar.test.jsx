import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import { OutputToolbar } from '.';
import mockJobData from '../../shared/data.job.json';

describe('<OutputToolbar />', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = mountWithContexts(
      <OutputToolbar
        job={{
          ...mockJobData,
          host_status_counts: {
            dark: 1,
            failures: 2,
          },
        }}
        onDelete={() => {}}
      />
    );
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(wrapper.length).toBe(1);
  });

  test('should hide badge counts based on job type', () => {
    wrapper = mountWithContexts(
      <OutputToolbar
        job={{ ...mockJobData, type: 'system_job' }}
        onDelete={() => {}}
      />
    );
    expect(wrapper.find('div[aria-label="Play Count"]').length).toBe(0);
    expect(wrapper.find('div[aria-label="Task Count"]').length).toBe(0);
    expect(wrapper.find('div[aria-label="Host Count"]').length).toBe(0);
    expect(
      wrapper.find('div[aria-label="Unreachable Host Count"]').length
    ).toBe(0);
    expect(wrapper.find('div[aria-label="Failed Host Count"]').length).toBe(0);
    expect(wrapper.find('div[aria-label="Elapsed Time"]').length).toBe(1);
  });

  test('should hide badge if count is equal to zero', () => {
    wrapper = mountWithContexts(
      <OutputToolbar
        job={{
          ...mockJobData,
          host_status_counts: {},
          playbook_counts: {},
        }}
        onDelete={() => {}}
      />
    );

    expect(wrapper.find('div[aria-label="Play Count"]').length).toBe(0);
    expect(wrapper.find('div[aria-label="Task Count"]').length).toBe(0);
    expect(wrapper.find('div[aria-label="Host Count"]').length).toBe(0);
    expect(
      wrapper.find('div[aria-label="Unreachable Host Count"]').length
    ).toBe(0);
    expect(wrapper.find('div[aria-label="Failed Host Count"]').length).toBe(0);
  });

  test('should display elapsed time as HH:MM:SS', () => {
    wrapper = mountWithContexts(
      <OutputToolbar
        job={{
          ...mockJobData,
          elapsed: 274265,
        }}
        onDelete={() => {}}
      />
    );

    expect(wrapper.find('div[aria-label="Elapsed Time"] Badge').text()).toBe(
      '76:11:05'
    );
  });

  test('should hide relaunch button based on user capabilities', () => {
    expect(wrapper.find('LaunchButton').length).toBe(1);
    wrapper = mountWithContexts(
      <OutputToolbar
        job={{
          ...mockJobData,
          summary_fields: {
            user_capabilities: {
              start: false,
            },
          },
        }}
        onDelete={() => {}}
      />
    );
    expect(wrapper.find('LaunchButton').length).toBe(0);
  });

  test('should hide delete button based on user capabilities', () => {
    expect(wrapper.find('DeleteButton').length).toBe(1);
    wrapper = mountWithContexts(
      <OutputToolbar
        job={{
          ...mockJobData,
          summary_fields: {
            user_capabilities: {
              delete: false,
            },
          },
        }}
        onDelete={() => {}}
      />
    );
    expect(wrapper.find('DeleteButton').length).toBe(0);
  });
});
