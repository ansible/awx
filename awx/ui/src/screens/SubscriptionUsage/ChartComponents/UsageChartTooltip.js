import * as d3 from 'd3';
import { t } from '@lingui/macro';

class UsageChartTooltip {
  constructor(opts) {
    this.label = opts.label;
    this.svg = opts.svg;
    this.colors = opts.colors;

    this.draw();
  }

  draw() {
    this.toolTipBase = d3.select(`${this.svg} > svg`).append('g');
    this.toolTipBase.attr('id', 'chart-tooltip');
    this.toolTipBase.attr('overflow', 'visible');
    this.toolTipBase.style('opacity', 0);
    this.toolTipBase.style('pointer-events', 'none');
    this.toolTipBase.attr('transform', 'translate(100, 100)');
    this.boxWidth = 200;
    this.textWidthThreshold = 20;

    this.toolTipPoint = this.toolTipBase
      .append('rect')
      .attr('transform', 'translate(10, -10) rotate(45)')
      .attr('x', 0)
      .attr('y', 0)
      .attr('height', 20)
      .attr('width', 20)
      .attr('fill', '#393f44');
    this.boundingBox = this.toolTipBase
      .append('rect')
      .attr('x', 10)
      .attr('y', -41)
      .attr('rx', 2)
      .attr('height', 82)
      .attr('width', this.boxWidth)
      .attr('fill', '#393f44');
    this.circleBlue = this.toolTipBase
      .append('circle')
      .attr('cx', 26)
      .attr('cy', 0)
      .attr('r', 7)
      .attr('stroke', 'white')
      .attr('fill', this.colors(1));
    this.circleRed = this.toolTipBase
      .append('circle')
      .attr('cx', 26)
      .attr('cy', 26)
      .attr('r', 7)
      .attr('stroke', 'white')
      .attr('fill', this.colors(0));
    this.consumedText = this.toolTipBase
      .append('text')
      .attr('x', 43)
      .attr('y', 4)
      .attr('font-size', 12)
      .attr('fill', 'white')
      .text(t`Subscriptions consumed`);
    this.capacityText = this.toolTipBase
      .append('text')
      .attr('x', 43)
      .attr('y', 28)
      .attr('font-size', 12)
      .attr('fill', 'white')
      .text(t`Subscription capacity`);
    this.icon = this.toolTipBase
      .append('text')
      .attr('fill', 'white')
      .attr('stroke', 'white')
      .attr('x', 24)
      .attr('y', 30)
      .attr('font-size', 12);
    this.consumed = this.toolTipBase
      .append('text')
      .attr('fill', 'white')
      .attr('font-size', 12)
      .attr('x', 122)
      .attr('y', 4)
      .attr('id', 'consumed-count')
      .text('0');
    this.capacity = this.toolTipBase
      .append('text')
      .attr('fill', 'white')
      .attr('font-size', 12)
      .attr('x', 122)
      .attr('y', 28)
      .attr('id', 'capacity-count')
      .text('0');
    this.date = this.toolTipBase
      .append('text')
      .attr('fill', 'white')
      .attr('stroke', 'white')
      .attr('x', 20)
      .attr('y', -21)
      .attr('font-size', 12);
  }

  handleMouseOver = (event, data) => {
    let consumed = 0;
    let capacity = 0;
    const [x, y] = d3.pointer(event);
    const tooltipPointerX = x + 75;

    const formatTooltipDate = d3.timeFormat('%m/%y');
    if (!event) {
      return;
    }

    const toolTipWidth = this.toolTipBase.node().getBoundingClientRect().width;
    const chartWidth = d3
      .select(`${this.svg}> svg`)
      .node()
      .getBoundingClientRect().width;
    const overflow = 100 - (toolTipWidth / chartWidth) * 100;
    const flipped = overflow < (tooltipPointerX / chartWidth) * 100;
    if (data) {
      consumed = data.CONSUMED || 0;
      capacity = data.CAPACITY || 0;
      this.date.text(formatTooltipDate(data.MONTH || null));
    }

    this.capacity.text(`${capacity}`);
    this.consumed.text(`${consumed}`);
    this.consumedTextWidth = this.consumed.node().getComputedTextLength();
    this.capacityTextWidth = this.capacity.node().getComputedTextLength();

    const maxTextPerc = (this.jobsWidth / this.boxWidth) * 100;
    const threshold = 40;
    const overage = maxTextPerc / threshold;
    let adjustedWidth;
    if (maxTextPerc > threshold) {
      adjustedWidth = this.boxWidth * overage;
    } else {
      adjustedWidth = this.boxWidth;
    }

    this.boundingBox.attr('width', adjustedWidth);
    this.toolTipBase.attr('transform', `translate(${tooltipPointerX}, ${y})`);
    if (flipped) {
      this.toolTipPoint.attr('transform', 'translate(-20, -10) rotate(45)');
      this.boundingBox.attr('x', -adjustedWidth - 20);
      this.circleBlue.attr('cx', -adjustedWidth);
      this.circleRed.attr('cx', -adjustedWidth);
      this.icon.attr('x', -adjustedWidth - 2);
      this.consumedText.attr('x', -adjustedWidth + 17);
      this.capacityText.attr('x', -adjustedWidth + 17);
      this.consumed.attr('x', -this.consumedTextWidth - 20 - 12);
      this.capacity.attr('x', -this.capacityTextWidth - 20 - 12);
      this.date.attr('x', -adjustedWidth - 5);
    } else {
      this.toolTipPoint.attr('transform', 'translate(10, -10) rotate(45)');
      this.boundingBox.attr('x', 10);
      this.circleBlue.attr('cx', 26);
      this.circleRed.attr('cx', 26);
      this.icon.attr('x', 24);
      this.consumedText.attr('x', 43);
      this.capacityText.attr('x', 43);
      this.consumed.attr('x', adjustedWidth - this.consumedTextWidth);
      this.capacity.attr('x', adjustedWidth - this.capacityTextWidth);
      this.date.attr('x', 20);
    }

    this.toolTipBase.style('opacity', 1);
    this.toolTipBase.interrupt();
  };

  handleMouseOut = () => {
    this.toolTipBase
      .transition()
      .delay(15)
      .style('opacity', 0)
      .style('pointer-events', 'none');
  };
}

export default UsageChartTooltip;
