import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import ConstructedInventoryHint from './ConstructedInventoryHint';

jest.mock('../../../api');

describe('<ConstructedInventoryHint />', () => {
  test('should render link to docs', () => {
    render(<ConstructedInventoryHint />);
    expect(
      screen.getByRole('link', {
        name: 'View constructed inventory documentation here',
      })
    ).toBeInTheDocument();
  });

  test('should expand hint details', () => {
    const { container } = render(<ConstructedInventoryHint />);

    expect(container.querySelector('table')).not.toBeInTheDocument();
    expect(container.querySelector('code')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Info alert details' }));
    expect(container.querySelector('table')).toBeInTheDocument();
    expect(container.querySelector('code')).toBeInTheDocument();
  });

  test('should copy sample plugin code block', () => {
    Object.assign(navigator, {
      clipboard: {
        writeText: () => {},
      },
    });
    jest.spyOn(navigator.clipboard, 'writeText');

    render(<ConstructedInventoryHint />);
    fireEvent.click(screen.getByRole('button', { name: 'Info alert details' }));
    fireEvent.click(
      screen.getByRole('button', { name: 'Hosts by processor type' })
    );
    fireEvent.click(
      screen.getByRole('button', {
        name: 'Copy to clipboard',
      })
    );
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        'intel_hosts: "GenuineIntel" in ansible_processor'
      )
    );
  });
});
