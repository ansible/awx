import React from 'react';
import { act } from 'react-dom/test-utils';
import { ProjectsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ProjectSyncButton from './ProjectSyncButton';

jest.mock('../../../api');
jest.mock('hooks/useBrandName', () => ({
  __esModule: true,
  default: () => ({
    current: 'AWX',
  }),
}));
describe('ProjectSyncButton', () => {
  let wrapper;

  const children = (handleSync) => (
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
  test('disable button and set onClick to undefined on sync', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectSyncButton projectId={1} lastJobStatus="running">
          {children}
        </ProjectSyncButton>
      );
    });

    expect(wrapper.find('Button').prop('isDisabled')).toBe(true);
    expect(wrapper.find('Button').prop('onClick')).toBe(undefined);
  });
  test('should render tooltip on sync', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectSyncButton projectId={1} lastJobStatus="running">
          {children}
        </ProjectSyncButton>
      );
    });

    expect(wrapper.find('Tooltip')).toHaveLength(1);
    expect(wrapper.find('Tooltip').prop('content')).toEqual(
      'This project is currently on sync and cannot be clicked until sync process completed'
    );
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
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(1);
    await act(async () => {
      wrapper.find('ModalBoxCloseButton').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(0);
  });
});
