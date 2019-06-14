import React from 'react';
import { mountWithContexts, waitForElement } from '../../enzymeHelpers';
import TemplatesList, { _TemplatesList } from '../../../src/pages/Templates/TemplatesList';
import { UnifiedJobTemplatesAPI } from '../../../src/api';

jest.mock('../../../src/api');

const mockTemplates = [{
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
  beforeEach(() => {
    UnifiedJobTemplatesAPI.read.mockResolvedValue({
      data: {
        count: mockTemplates.length,
        results: mockTemplates
      }
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders succesfully', () => {
    mountWithContexts(
      <TemplatesList
        match={{ path: '/templates', url: '/templates' }}
        location={{ search: '', pathname: '/templates' }}
      />
    );
  });

  test('Templates are retrieved from the api and the components finishes loading', async (done) => {
    const loadUnifiedJobTemplates = jest.spyOn(_TemplatesList.prototype, 'loadUnifiedJobTemplates');
    const wrapper = mountWithContexts(<TemplatesList />);
    await waitForElement(wrapper, 'TemplatesList', (el) => el.state('contentLoading') === true);
    expect(loadUnifiedJobTemplates).toHaveBeenCalled();
    await waitForElement(wrapper, 'TemplatesList', (el) => el.state('contentLoading') === false);
    done();
  });

  test('handleSelect is called when a template list item is selected', async (done) => {
    const handleSelect = jest.spyOn(_TemplatesList.prototype, 'handleSelect');
    const wrapper = mountWithContexts(<TemplatesList />);
    await waitForElement(wrapper, 'TemplatesList', (el) => el.state('contentLoading') === false);
    wrapper.find('DataListCheck#select-jobTemplate-1').props().onChange();
    expect(handleSelect).toBeCalled();
    await waitForElement(wrapper, 'TemplatesList', (el) => el.state('selected').length === 1);
    done();
  });

  test('handleSelectAll is called when a template list item is selected', async (done) => {
    const handleSelectAll = jest.spyOn(_TemplatesList.prototype, 'handleSelectAll');
    const wrapper = mountWithContexts(<TemplatesList />);
    await waitForElement(wrapper, 'TemplatesList', (el) => el.state('contentLoading') === false);
    wrapper.find('Checkbox#select-all').props().onChange(true);
    expect(handleSelectAll).toBeCalled();
    await waitForElement(wrapper, 'TemplatesList', (el) => el.state('selected').length === 3);
    done();
  });
});
