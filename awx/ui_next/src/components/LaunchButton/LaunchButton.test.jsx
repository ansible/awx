import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import LaunchButton from './LaunchButton';
import { JobTemplatesAPI } from '@api';

jest.mock('@api');

describe('LaunchButton', () => {
  JobTemplatesAPI.readLaunch.mockResolvedValue({
    data: {
      can_start_without_user_input: true,
    },
  });

  const children = ({ handleLaunch }) => (
    <button type="submit" onClick={() => handleLaunch()} />
  );

  const resource = {
    id: 1,
    type: 'job_template',
  };

  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <LaunchButton resource={resource}>{children}</LaunchButton>
    );
    expect(wrapper).toHaveLength(1);
  });

  test('should redirect to job after successful launch', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/jobs/9000'],
    });
    JobTemplatesAPI.launch.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    const wrapper = mountWithContexts(
      <LaunchButton resource={resource}>{children}</LaunchButton>,
      {
        context: {
          router: { history },
        },
      }
    );
    const button = wrapper.find('button');
    button.prop('onClick')();
    expect(JobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
    await sleep(0);
    expect(JobTemplatesAPI.launch).toHaveBeenCalledWith(1);
    expect(history.location.pathname).toEqual('/jobs/9000');
  });

  test('displays error modal after unsuccessful launch', async () => {
    JobTemplatesAPI.launch.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/job_templates/1/launch',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    const wrapper = mountWithContexts(
      <LaunchButton resource={resource}>{children}</LaunchButton>
    );
    expect(wrapper.find('Modal').length).toBe(0);
    wrapper.find('button').prop('onClick')();
    await sleep(0);
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(1);
    wrapper.find('ModalBoxCloseButton').simulate('click');
    await sleep(0);
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(0);
  });
});
