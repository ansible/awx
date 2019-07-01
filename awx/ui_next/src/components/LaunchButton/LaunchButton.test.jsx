import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
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
  const children = handleLaunch => (
    <button type="submit" onClick={handleLaunch} />
  );

  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <LaunchButton templateId={1}>{children}</LaunchButton>
    );
    expect(wrapper).toHaveLength(1);
  });
  test('redirects to details after successful launch', async done => {
    const history = {
      push: jest.fn(),
    };
    JobTemplatesAPI.launch.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    const wrapper = mountWithContexts(
      <LaunchButton templateId={1}>{children}</LaunchButton>,
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
    expect(history.push).toHaveBeenCalledWith('/jobs/9000/details');
    done();
  });
  test('displays error modal after unsuccessful launch', async done => {
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
      <LaunchButton templateId={1}>{children}</LaunchButton>
    );
    const button = wrapper.find('button');
    button.prop('onClick')();
    await waitForElement(
      wrapper,
      'Modal.at-c-alertModal--danger',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );
    const modalCloseButton = wrapper.find('ModalBoxCloseButton');
    modalCloseButton.simulate('click');
    await waitForElement(
      wrapper,
      'Modal.at-c-alertModal--danger',
      el => el.props().isOpen === false
    );
    done();
  });
});
