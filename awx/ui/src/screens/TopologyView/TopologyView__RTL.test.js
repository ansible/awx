import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { MeshAPI } from 'api';
import { render, waitFor, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import TopologyView from './TopologyView';

jest.mock('../../api');
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
        onmessage: function handleWorkerEvent(event) {
          switch (event.data.type) {
            case 'tick':
              return jest.fn(event.data);
            case 'end':
              return jest.fn(event.data);
            default:
              return false;
          }
        },
      };
    },
  };
});
afterEach(() => {
  jest.clearAllMocks();
});
describe('<TopologyView />', () => {
  test('should render properly', async () => {
    MeshAPI.read.mockResolvedValue({
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
    });
    render(
      <MemoryRouter>
        <TopologyView />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByRole('heading', { level: 2 }));
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent(
      'Topology View'
    );
    expect(screen.getByLabelText('mesh-svg')).toBeVisible();
  });
  test('should render with 0 nodes', async () => {
    MeshAPI.read.mockResolvedValue({
      data: {
        nodes: [],
        links: [],
      },
    });
    render(
      <MemoryRouter>
        <TopologyView />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByRole('heading', { level: 2 }));
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent(
      'Topology View'
    );
    expect(screen.getByLabelText('mesh-svg')).toBeVisible();
  });
  test('should handle API error', async () => {
    MeshAPI.read.mockRejectedValueOnce(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2/mesh_visualizer',
          },
          data: 'An error occurred',
          status: 500,
        },
      })
    );
    render(
      <MemoryRouter>
        <TopologyView />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByRole('heading', { level: 2 }));
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent(
      'Topology View'
    );
    expect(screen.getByText(/something went wrong/i)).toBeVisible();
  });
});
