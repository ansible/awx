import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { sleep } from '../../../../testUtils/testUtils';

import ProjectSyncButton from './ProjectSyncButton';
import { ProjectsAPI } from '../../../api';

jest.mock('../../../api');

describe('ProjectSyncButton', () => {
  ProjectsAPI.readSync.mockResolvedValue({
    data: {
      can_update: true,
    },
  });

  const children = handleSync => (
    <button type="submit" onClick={() => handleSync()} />
  );

  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <ProjectSyncButton projectId={1}>{children}</ProjectSyncButton>
    );
    expect(wrapper).toHaveLength(1);
  });
  test('correct api calls are made on sync', async done => {
    ProjectsAPI.sync.mockResolvedValue({
      data: {
        id: 9000,
      },
    });
    const wrapper = mountWithContexts(
      <ProjectSyncButton projectId={1}>{children}</ProjectSyncButton>
    );
    const button = wrapper.find('button');
    button.prop('onClick')();
    expect(ProjectsAPI.readSync).toHaveBeenCalledWith(1);
    await sleep(0);
    expect(ProjectsAPI.sync).toHaveBeenCalledWith(1);
    done();
  });
  test('displays error modal after unsuccessful sync', async done => {
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
    const wrapper = mountWithContexts(
      <ProjectSyncButton projectId={1}>{children}</ProjectSyncButton>
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
    done();
  });
});
