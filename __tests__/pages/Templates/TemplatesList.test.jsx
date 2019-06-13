import React from 'react';
import { mountWithContexts } from '../../enzymeHelpers';
import TemplatesList, { _TemplatesList } from '../../../src/pages/Templates/TemplatesList';

jest.mock('../../../src/api');

const setDefaultState = (templatesList) => {
  templatesList.setState({
    itemCount: mockUnifiedJobTemplatesFromAPI.length,
    isLoading: false,
    isInitialized: true,
    selected: [],
    templates: mockUnifiedJobTemplatesFromAPI,
  });
  templatesList.update();
};

const mockUnifiedJobTemplatesFromAPI = [{
  id: 1,
  name: 'Template 1',
  url: '/templates/job_template/1',
  type: 'job_template',
  summary_fields: {
    inventory: {},
    project: {},
  }
},
{
  id: 2,
  name: 'Template 2',
  url: '/templates/job_template/2',
  type: 'job_template',
  summary_fields: {
    inventory: {},
    project: {},
  }
},
{
  id: 3,
  name: 'Template 3',
  url: '/templates/job_template/3',
  type: 'job_template',
  summary_fields: {
    inventory: {},
    project: {},
  }
}];

describe('<TemplatesList />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <TemplatesList
        match={{ path: '/templates', url: '/templates' }}
        location={{ search: '', pathname: '/templates' }}
      />
    );
  });
  test('Templates are retrieved from the api and the components finishes loading', async (done) => {
    const readTemplates = jest.spyOn(_TemplatesList.prototype, 'readUnifiedJobTemplates');

    const wrapper = mountWithContexts(<TemplatesList />).find('TemplatesList');

    expect(wrapper.state('isLoading')).toBe(true);
    await expect(readTemplates).toHaveBeenCalled();
    wrapper.update();
    expect(wrapper.state('isLoading')).toBe(false);
    done();
  });

  test('handleSelect is called when a template list item is selected', async () => {
    const handleSelect = jest.spyOn(_TemplatesList.prototype, 'handleSelect');

    const wrapper = mountWithContexts(<TemplatesList />);

    const templatesList = wrapper.find('TemplatesList');
    setDefaultState(templatesList);

    expect(templatesList.state('isLoading')).toBe(false);
    wrapper.find('DataListCheck#select-jobTemplate-1').props().onChange();
    expect(handleSelect).toBeCalled();
    templatesList.update();
    expect(templatesList.state('selected').length).toBe(1);
  });

  test('handleSelectAll is called when a template list item is selected', async () => {
    const handleSelectAll = jest.spyOn(_TemplatesList.prototype, 'handleSelectAll');

    const wrapper = mountWithContexts(<TemplatesList />);

    const templatesList = wrapper.find('TemplatesList');
    setDefaultState(templatesList);

    expect(templatesList.state('isLoading')).toBe(false);
    wrapper.find('Checkbox#select-all').props().onChange(true);
    expect(handleSelectAll).toBeCalled();
    wrapper.update();
    expect(templatesList.state('selected').length).toEqual(templatesList.state('templates')
      .length);
  });
});
