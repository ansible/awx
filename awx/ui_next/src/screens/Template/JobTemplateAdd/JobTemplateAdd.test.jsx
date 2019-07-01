import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import JobTemplateAdd from './JobTemplateAdd';

jest.mock('@api');

describe('<JobTemplateAdd />', () => {
  const defaultProps = {
    description: '',
    inventory: 0,
    job_type: 'run',
    name: '',
    playbook: '',
    project: 0,
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render Job Template Form', () => {
    const wrapper = mountWithContexts(<JobTemplateAdd />);
    expect(wrapper.find('JobTemplateForm').length).toBe(1);
  });

  test('should render Job Template Form with default values', () => {
    const wrapper = mountWithContexts(<JobTemplateAdd />);
    expect(wrapper.find('input#template-description').props().value).toBe(
      defaultProps.description
    );
    expect(wrapper.find('input#template-inventory').props().value).toBe(
      defaultProps.inventory
    );
    expect(wrapper.find('AnsibleSelect[name="job_type"]').props().value).toBe(
      defaultProps.job_type
    );
    expect(wrapper.find('input#template-name').props().value).toBe(
      defaultProps.name
    );
    expect(wrapper.find('input#template-playbook').props().value).toBe(
      defaultProps.playbook
    );
    expect(wrapper.find('input#template-project').props().value).toBe(
      defaultProps.project
    );
  });

  test('should navigate to templates list when cancel is clicked', () => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mountWithContexts(<JobTemplateAdd />, {
      context: { router: { history } },
    });

    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(history.push).toHaveBeenCalledWith('/templates');
  });
});
