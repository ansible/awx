import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import LaunchButton from './LaunchButton';
import { JobTemplatesAPI } from '@api';

jest.mock('@api');

describe('LaunchButton', () => {
  JobTemplatesAPI.readLaunch.mockResolvedValue({
    data: {
      can_start_without_user_input: true
    }
  });

  test('renders the expected content', () => {
    const wrapper = mountWithContexts(<LaunchButton templateId={1} />);
    expect(wrapper).toHaveLength(1);
  });
  test('redirects to details after successful launch', async (done) => {
    const history = {
      push: jest.fn(),
    };
    JobTemplatesAPI.launch.mockResolvedValue({
      data: {
        id: 9000
      }
    });
    const wrapper = mountWithContexts(
      <LaunchButton templateId={1} />, {
        context: {
          router: { history }
        }
      }
    );
    const launchButton = wrapper.find('LaunchButton__StyledLaunchButton');
    launchButton.simulate('click');
    await sleep(0);
    expect(JobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
    expect(JobTemplatesAPI.launch).toHaveBeenCalledWith(1);
    expect(history.push).toHaveBeenCalledWith('/jobs/9000/details');
    done();
  });
  test('displays error modal after unsuccessful launch', async (done) => {
    JobTemplatesAPI.launch.mockRejectedValue({});
    const wrapper = mountWithContexts(<LaunchButton templateId={1} />);
    const launchButton = wrapper.find('LaunchButton__StyledLaunchButton');
    launchButton.simulate('click');
    await waitForElement(wrapper, 'Modal.at-c-alertModal--danger', (el) => el.props().isOpen === true && el.props().title === 'Error!');
    const modalCloseButton = wrapper.find('ModalBoxCloseButton');
    modalCloseButton.simulate('click');
    await waitForElement(wrapper, 'Modal.at-c-alertModal--danger', (el) => el.props().isOpen === false);
    done();
  });
});
