import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ProjectsAPI } from 'api';
import PlaybookSelect from './PlaybookSelect';

jest.mock('api');

describe('<PlaybookSelect />', () => {
  beforeEach(() => {
    ProjectsAPI.readPlaybooks.mockReturnValue({
      data: ['debug.yml', 'test.yml'],
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('should reload playbooks when project value changes', async () => {
    const { rerender } = render(
      <PlaybookSelect
        projectId={1}
        isValid
        onChange={() => {}}
        onError={() => {}}
      />
    );

    await waitFor(() => {
      expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledWith(1);
    });

    rerender(
      <PlaybookSelect
        projectId={15}
        isValid
        onChange={() => {}}
        onError={() => {}}
      />
    );

    await waitFor(() => {
      expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledTimes(2);
      expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledWith(15);
    });
  });

  test('should trigger the onChange callback for the option selected from the list', async () => {
    const mockCallback = jest.fn();

    const { container } = render(
      <PlaybookSelect
        projectId={1}
        isValid={true}
        onChange={mockCallback}
        onError={() => {}}
      />
    );

    await waitFor(() => {
      const selectToggleButton = container.querySelector(
        'button.pf-c-select__toggle-button'
      );
      fireEvent.click(selectToggleButton);
      // Select options are displayed
      expect(screen.getAllByRole('option').length).toBe(2);

      fireEvent.click(screen.getByText('debug.yml'));

      expect(mockCallback).toHaveBeenCalledWith('debug.yml');
    });
  });

  test('should allow entering playbook file name manually', async () => {
    const mockCallback = jest.fn();

    const { container } = render(
      <PlaybookSelect
        projectId={1}
        isValid={true}
        onChange={mockCallback}
        onError={() => {}}
      />
    );

    await waitFor(() => {
      const input = container.querySelector('input.pf-c-form-control');
      expect(input).toBeVisible();
      fireEvent.change(input, { target: { value: 'foo.yml' } });
    });

    await waitFor(() => {
      // A new select option is displayed ("foo.yml")
      expect(
        screen.getByText('"foo.yml"', { selector: '[role="option"]' })
      ).toBeVisible();
      expect(screen.getAllByRole('option').length).toBe(1);

      fireEvent.click(
        screen.getByText('"foo.yml"', { selector: '[role="option"]' })
      );

      expect(mockCallback).toHaveBeenCalledWith('foo.yml');
    });
  });
});
