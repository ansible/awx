import * as d3 from 'd3';
import { MESH_FORCE_LAYOUT } from '../../constants';

onmessage = function calculateLayout({ data: { nodes, links } }) {
  const simulation = d3
    .forceSimulation(nodes)
    .force(
      'charge',
      d3
        .forceManyBody(MESH_FORCE_LAYOUT.defaultForceBody)
        .strength(MESH_FORCE_LAYOUT.defaultForceStrength)
    )
    .force(
      'link',
      d3.forceLink(links).id((d) => d.hostname)
    )
    .force('collide', d3.forceCollide(MESH_FORCE_LAYOUT.defaultCollisionFactor))
    .force('forceX', d3.forceX(MESH_FORCE_LAYOUT.defaultForceX))
    .force('forceY', d3.forceY(MESH_FORCE_LAYOUT.defaultForceY))
    .stop();

  for (
    let i = 0,
      n = Math.ceil(
        Math.log(simulation.alphaMin()) / Math.log(1 - simulation.alphaDecay())
      );
    i < n;
    ++i
  ) {
    postMessage({ type: 'tick', progress: i / n });
    simulation.tick();
  }

  postMessage({ type: 'end', nodes, links });
};
