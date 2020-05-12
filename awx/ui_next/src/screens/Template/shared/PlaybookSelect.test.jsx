import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import PlaybookSelect from './PlaybookSelect';
import { ProjectsAPI } from '../../../api';

jest.mock('../../../api');

describe('<PlaybookSelect />', () => {
  beforeEach(() => {
    ProjectsAPI.readPlaybooks.mockReturnValue({
      data: ['debug.yml'],
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('should reload playbooks when project value changes', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <PlaybookSelect
          projectId={1}
          isValid
          form={{}}
          field={{ onChange: () => {}, value: '' }}
          onError={() => {}}
        />
      );
    });

    expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledWith(1);
    await act(async () => {
      wrapper.setProps({ projectId: 15 });
    });

    expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledTimes(2);
    expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledWith(15);
  });
});
