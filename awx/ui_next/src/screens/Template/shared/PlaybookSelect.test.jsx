import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import PlaybookSelect from './PlaybookSelect';
import { ProjectsAPI } from '@api';

jest.mock('@api');

describe('<PlaybookSelect />', () => {
  beforeEach(() => {
    ProjectsAPI.readPlaybooks.mockReturnValue({
      data: ['debug.yml'],
    });
  });

  test('should reload playbooks when project value changes', () => {
    const wrapper = mountWithContexts(
      <PlaybookSelect
        projectId={1}
        isValid
        form={{}}
        field={{}}
        onError={() => {}}
      />
    );

    expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledWith(1);
    wrapper.setProps({ projectId: 15 });

    expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledTimes(2);
    expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledWith(15);
  });
});
