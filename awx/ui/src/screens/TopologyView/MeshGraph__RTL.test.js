import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { render, waitFor, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MeshGraph from './MeshGraph';

jest.mock('util/webWorker', () => {
  return {
    __esModule: true,
    default: () => {
      return {
        postMessage: jest.fn().mockReturnValueOnce({
          data: {
            type: 'end',
            links: [],
            nodes: [
              {
                id: 1,
                hostname: 'foo',
                node_type: 'control',
                node_state: 'healthy',
                index: 0,
                vx: -1,
                vy: -5,
                x: 400,
                y: 300,
              },
              {
                id: 2,
                hostname: 'bar',
                node_type: 'control',
                node_state: 'healthy',
                index: 1,
                vx: -1,
                vy: -5,
                x: 500,
                y: 200,
              },
            ],
          },
        }),
        onmessage: jest.fn(),
      };
    },
  };
});
afterEach(() => {
  jest.clearAllMocks();
});
describe('<MeshGraph />', () => {
  test('renders correctly', async () => {
    const mockData = {
      data: {
        nodes: [
          {
            id: 1,
            hostname: 'foo',
            node_type: 'control',
            node_state: 'healthy',
          },
          {
            id: 2,
            hostname: 'bar',
            node_type: 'control',
            node_state: 'healthy',
          },
        ],
        links: [],
      },
    };
    const mockZoomFn = jest.fn();
    const mockSetZoomCtrFn = jest.fn();
    render(
      <MemoryRouter>
        <MeshGraph
          data={mockData}
          showLegend={true}
          zoom={mockZoomFn}
          setShowZoomControls={mockSetZoomCtrFn}
        />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByLabelText('mesh-svg'));
    expect(screen.getByLabelText('mesh-svg')).toBeVisible();
  });
});
