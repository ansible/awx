import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { sleep } from '../../../../testUtils/testUtils';

import ProjectSyncButton from './ProjectSyncButton';
import { ProjectsAPI } from '../../../api';

jest.mock('../../../api');

describe('ProjectSyncButton', () => {
  let wrapper;

  const children = handleSync => (
    <button type="submit" onClick={() => handleSync()} />
  );

  test('renders the expected content', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectSyncButton projectId={1}>{children}</ProjectSyncButton>
      );
    });
    expect(wrapper).toHaveLength(1);
  });
  test('correct api calls are made on sync', async () => {
    ProjectsAPI.sync.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectSyncButton projectId={1}>{children}</ProjectSyncButton>
      );
    });
    const button = wrapper.find('button');
    await act(async () => {
      button.prop('onClick')();
    });

    expect(ProjectsAPI.sync).toHaveBeenCalledWith(1);
  });
  test('displays error modal after unsuccessful sync', async () => {
    ProjectsAPI.sync.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/projects/1/update',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectSyncButton projectId={1}>{children}</ProjectSyncButton>
      );
    });
    expect(wrapper.find('Modal').length).toBe(0);
    await act(async () => {
      wrapper.find('button').prop('onClick')();
    });
    await sleep(0);
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(1);
    await act(async () => {
      wrapper.find('ModalBoxCloseButton').simulate('click');
    });
    await sleep(0);
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(0);
  });
});
