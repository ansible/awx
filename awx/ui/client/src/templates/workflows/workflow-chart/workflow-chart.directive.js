/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$state','moment', '$timeout', '$window', '$filter', 'Rest', 'GetBasePath', 'ProcessErrors', 'TemplatesStrings',
    function($state, moment, $timeout, $window, $filter, Rest, GetBasePath, ProcessErrors, TemplatesStrings) {

    return {
        scope: {
            treeData: '=',
            canAddWorkflowJobTemplate: '=',
            workflowJobTemplateObj: '=',
            addNode: '&',
            editNode: '&',
            deleteNode: '&',
            editLink: '&',
            workflowZoomed: '&',
            mode: '@'
        },
        restrict: 'E',
        link: function(scope, element) {

            let marginLeft = 20,
                i = 0,
                nodeW = 180,
                nodeH = 60,
                rootW = 60,
                rootH = 40,
                startNodeOffsetY = scope.mode === 'details' ? 17 : 10,
                verticalSpaceBetweenNodes = 20,
                maxNodeTextLength = 27,
                windowHeight,
                windowWidth,
                tree,
                line,
                zoomObj,
                baseSvg,
                svgGroup,
                graphLoaded;

            scope.dimensionsSet = false;

            $timeout(function(){
                let dimensions = calcAvailableScreenSpace();

                windowHeight = dimensions.height;
                windowWidth = dimensions.width;

                $('.WorkflowMaker-chart').css("height", windowHeight);
                $('.WorkflowMaker-chart').css("width", windowWidth);

                scope.dimensionsSet = true;

                init();
            });

            function init() {
                tree = d3.layout.tree()
                        .nodeSize([nodeH + verticalSpaceBetweenNodes,nodeW])
                        .separation(function(a, b) {
                            // This should tighten up some of the other nodes so there's not so much wasted space
                            return a.parent === b.parent ? 1 : 1.25;
                        });

                line = d3.svg.line()
                         .x(function(d){return d.x;})
                         .y(function(d){return d.y;});

                zoomObj = d3.behavior.zoom().scaleExtent([0.5, 2]);

                baseSvg = d3.select(element[0]).append("svg")
                    .attr("class", "WorkflowChart-svg")
                    .call(zoomObj
                        .on("zoom", naturalZoom)
                    );

                svgGroup = baseSvg.append("g")
                    .attr("id", "aw-workflow-chart-g")
                    .attr("transform", "translate(" + marginLeft + "," + (windowHeight/2 - rootH/2 - startNodeOffsetY) + ")");
            }

            function calcAvailableScreenSpace() {
                let dimensions = {};

                if(scope.mode !== 'details') {
                    // This is the workflow editor
                    dimensions.height = $('.WorkflowMaker-contentLeft').outerHeight() - $('.WorkflowLegend-maker').outerHeight();
                    dimensions.width = $('#workflow-modal-dialog').width() - $('.WorkflowMaker-contentRight').outerWidth();
                }
                else {
                    // This is the workflow details view
                    let panel = $('.WorkflowResults-rightSide').children('.Panel')[0];
                    let panelWidth = $(panel).width();
                    let panelHeight = $(panel).height();
                    let headerHeight = $('.StandardOut-panelHeader').outerHeight();
                    let legendHeight = $('.WorkflowLegend-details').outerHeight();
                    let proposedHeight = panelHeight - headerHeight - legendHeight - 40;

                    dimensions.height = proposedHeight > 200 ? proposedHeight : 200;
                    dimensions.width = panelWidth;
                }

                return dimensions;
            }

            function lineData(d){

                let sourceX = d.source.isStartNode ? d.source.y + rootW : d.source.y + nodeW;
                let sourceY = d.source.isStartNode ? d.source.x + startNodeOffsetY + rootH / 2 : d.source.x + nodeH / 2;
                let targetX = d.target.y;
                let targetY = d.target.x + nodeH / 2;

                let points = [
                    {
                        x: sourceX,
                        y: sourceY
                    },
                    {
                        x: targetX,
                        y: targetY
                    }
                ];

                return line(points);
            }

            // TODO: this function is hacky and we need to come up with a better solution
            // see: http://stackoverflow.com/questions/15975440/add-ellipses-to-overflowing-text-in-svg#answer-27723752
            function wrap(text) {
                if(text && text.length > maxNodeTextLength) {
                    return text.substring(0,maxNodeTextLength) + '...';
                }
                else {
                    return text;
                }
            }

            function rounded_rect(x, y, w, h, r, tl, tr, bl, br) {
                var retval;
                retval  = "M" + (x + r) + "," + y;
                retval += "h" + (w - 2*r);
                if (tr) { retval += "a" + r + "," + r + " 0 0 1 " + r + "," + r; }
                else { retval += "h" + r; retval += "v" + r; }
                retval += "v" + (h - 2*r);
                if (br) { retval += "a" + r + "," + r + " 0 0 1 " + -r + "," + r; }
                else { retval += "v" + r; retval += "h" + -r; }
                retval += "h" + (2*r - w);
                if (bl) { retval += "a" + r + "," + r + " 0 0 1 " + -r + "," + -r; }
                else { retval += "h" + -r; retval += "v" + -r; }
                retval += "v" + (2*r - h);
                if (tl) { retval += "a" + r + "," + r + " 0 0 1 " + r + "," + -r; }
                else { retval += "v" + -r; retval += "h" + r; }
                retval += "z";
                return retval;
            }

            // This is the zoom function called by using the mousewheel/click and drag
            function naturalZoom() {
                let scale = d3.event.scale,
                    translation = d3.event.translate;

                translation = [translation[0] + (marginLeft*scale), translation[1] + ((windowHeight/2 - rootH/2 - startNodeOffsetY)*scale)];

                svgGroup.attr("transform", "translate(" + translation + ")scale(" + scale + ")");

                scope.workflowZoomed({
                    zoom: scale
                });
            }

            // This is the zoom that gets called when the user interacts with the manual zoom controls
            function manualZoom(zoom) {
                let scale = zoom / 100,
                translation = zoomObj.translate(),
                origZoom = zoomObj.scale(),
                unscaledOffsetX = (translation[0] + ((windowWidth*origZoom) - windowWidth)/2)/origZoom,
                unscaledOffsetY = (translation[1] + ((windowHeight*origZoom) - windowHeight)/2)/origZoom,
                translateX = unscaledOffsetX*scale - ((scale*windowWidth)-windowWidth)/2,
                translateY = unscaledOffsetY*scale - ((scale*windowHeight)-windowHeight)/2;

                svgGroup.attr("transform", "translate(" + [translateX + (marginLeft*scale), translateY + ((windowHeight/2 - rootH/2 - startNodeOffsetY)*scale)] + ")scale(" + scale + ")");
                zoomObj.scale(scale);
                zoomObj.translate([translateX, translateY]);
            }

            function manualPan(direction) {
                let scale = zoomObj.scale(),
                    distance = 150 * scale,
                    translateX,
                    translateY,
                    translateCoords = zoomObj.translate();
                if (direction === 'left' || direction === 'right') {
                    translateX = direction === 'left' ? translateCoords[0] - distance : translateCoords[0] + distance;
                    translateY = translateCoords[1];
                } else if (direction === 'up' || direction === 'down') {
                    translateX = translateCoords[0];
                    translateY = direction === 'up' ? translateCoords[1] - distance : translateCoords[1] + distance;
                }
                svgGroup.attr("transform", "translate(" + translateX + "," + (translateY + ((windowHeight/2 - rootH/2 - startNodeOffsetY)*scale)) + ")scale(" + scale + ")");
                zoomObj.translate([translateX, translateY]);
            }

            function resetZoomAndPan() {
                svgGroup.attr("transform", "translate(" + marginLeft + "," + (windowHeight/2 - rootH/2 - startNodeOffsetY) + ")scale(" + 1 + ")");
                // Update the zoomObj
                zoomObj.scale(1);
                zoomObj.translate([0,0]);
            }

            function zoomToFitChart() {
                let graphDimensions = d3.select('#aw-workflow-chart-g')[0][0].getBoundingClientRect(),
                startNodeDimensions = d3.select('.WorkflowChart-rootNode')[0][0].getBoundingClientRect(),
                availableScreenSpace = calcAvailableScreenSpace(),
                currentZoomValue = zoomObj.scale(),
                unscaledH = graphDimensions.height/currentZoomValue,
                unscaledW = graphDimensions.width/currentZoomValue,
                scaleNeededForMaxHeight = (availableScreenSpace.height)/unscaledH,
                scaleNeededForMaxWidth = (availableScreenSpace.width - marginLeft)/unscaledW,
                lowerScale = Math.min(scaleNeededForMaxHeight, scaleNeededForMaxWidth),
                scaleToFit = lowerScale < 0.5 ? 0.5 : (lowerScale > 2 ? 2 : Math.floor(lowerScale * 10)/10),
                startNodeOffsetFromGraphCenter = Math.round((((rootH/2) + (startNodeDimensions.top/currentZoomValue)) - ((graphDimensions.top/currentZoomValue) + (unscaledH/2)))*scaleToFit);

                manualZoom(scaleToFit*100);

                scope.workflowZoomed({
                    zoom: scaleToFit
                });

                svgGroup.attr("transform", "translate(" + marginLeft + "," + (windowHeight/2 - (nodeH*scaleToFit/2) + startNodeOffsetFromGraphCenter) + ")scale(" + scaleToFit + ")");
                zoomObj.translate([marginLeft - scaleToFit*marginLeft, windowHeight/2 - (nodeH*scaleToFit/2) + startNodeOffsetFromGraphCenter - ((windowHeight/2 - rootH/2 - startNodeOffsetY)*scaleToFit)]);

            }

            function update() {
                let userCanAddEdit = (scope.workflowJobTemplateObj && scope.workflowJobTemplateObj.summary_fields && scope.workflowJobTemplateObj.summary_fields.user_capabilities && scope.workflowJobTemplateObj.summary_fields.user_capabilities.edit) || scope.canAddWorkflowJobTemplate;
                if(scope.dimensionsSet) {
                    // Declare the nodes
                    let nodes = tree.nodes(scope.treeData),
                        links = tree.links(nodes);

                    let node = svgGroup.selectAll("g.WorkflowChart-node")
                        .data(nodes, function(d) {
                            d.y = d.depth * 240;
                            return d.id || (d.id = ++i);
                        });

                    let nodeEnter = node.enter().append("g")
                        .attr("class", "WorkflowChart-node")
                        .attr("id", function(d){return "node-" + d.id;})
                        .attr("parent", function(d){return d.parent ? d.parent.id : null;})
                        .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

                    nodeEnter.each(function(d) {
                        let thisNode = d3.select(this);
                        if(d.isStartNode && scope.mode === 'details') {
                            // Overwrite the default root height and width and replace it with a small blue square
                            rootW = 25;
                            rootH = 25;
                            thisNode.append("rect")
                                .attr("width", rootW)
                                .attr("height", rootH)
                                .attr("y", startNodeOffsetY)
                                .attr("rx", 5)
                                .attr("ry", 5)
                                .attr("fill", "#337ab7")
                                .attr("class", "WorkflowChart-rootNode");
                        }
                        else if(d.isStartNode && scope.mode !== 'details') {
                            thisNode.append("rect")
                                .attr("width", rootW)
                                .attr("height", rootH)
                                .attr("y", 10)
                                .attr("rx", 5)
                                .attr("ry", 5)
                                .attr("fill", "#5cb85c")
                                .attr("class", "WorkflowChart-rootNode")
                                .call(add_node);
                            thisNode.append("text")
                                .attr("x", 13)
                                .attr("y", 30)
                                .attr("dy", ".35em")
                                .attr("class", "WorkflowChart-startText")
                                .text(function () { return TemplatesStrings.get('workflow_maker.START'); })
                                .call(add_node);
                        }
                        else {
                            thisNode.append("rect")
                                .attr("width", nodeW)
                                .attr("height", nodeH)
                                .attr("rx", 5)
                                .attr("ry", 5)
                                .attr('stroke', function(d) {
                                    if(d.job && d.job.status) {
                                        if(d.job.status === "successful"){
                                            return "#5cb85c";
                                        }
                                        else if (d.job.status === "failed" || d.job.status === "error" || d.job.status === "cancelled") {
                                            return "#d9534f";
                                        }
                                        else {
                                            return "#D7D7D7";
                                        }
                                    }
                                    else {
                                        return "#D7D7D7";
                                    }
                                })
                                .attr('stroke-width', "2px")
                                .attr("class", function(d) {
                                    let classString = d.placeholder ? "WorkflowChart-rect WorkflowChart-placeholder" : "WorkflowChart-rect";
                                    classString += !d.unifiedJobTemplate ? " WorkflowChart-dashedNode" : "";
                                    return classString;
                                });

                            thisNode.append("path")
                                .attr("d", rounded_rect(1, 0, 5, nodeH, 5, 1, 0, 1, 0))
                                .attr("class", "WorkflowChart-activeNode")
                                .style("display", function(d) { return d.isActiveEdit ? null : "none"; });

                            thisNode.append("text")
                                .attr("x", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? 20 : nodeW / 2; })
                                .attr("y", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? 10 : nodeH / 2; })
                                .attr("dy", ".35em")
                                .attr("text-anchor", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? "inherit" : "middle"; })
                                .attr("class", "WorkflowChart-defaultText WorkflowChart-nameText")
                                .text(function (d) {
                                    return (d.unifiedJobTemplate && d.unifiedJobTemplate.name) ? d.unifiedJobTemplate.name : "";
                                }).each(wrap);

                            thisNode.append("foreignObject")
                                .attr("x", 62)
                                .attr("y", 22)
                                .attr("dy", ".35em")
                                .attr("text-anchor", "middle")
                                .attr("class", "WorkflowChart-defaultText WorkflowChart-deletedText")
                                .html(function () {
                                    return `<span>${TemplatesStrings.get('workflow_maker.DELETED')}</span>`;
                                })
                                .style("display", function(d) { return d.unifiedJobTemplate || d.placeholder ? "none" : null; });

                            thisNode.append("circle")
                                .attr("cy", nodeH)
                                .attr("r", 10)
                                .attr("class", "WorkflowChart-nodeTypeCircle")
                                .style("display", function(d) { return d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update" || d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? null : "none"; });

                            thisNode.append("text")
                                .attr("y", nodeH)
                                .attr("dy", ".35em")
                                .attr("text-anchor", "middle")
                                .attr("class", "WorkflowChart-nodeTypeLetter")
                                .text(function (d) {
                                    return (d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update")) ? "P" : (d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? "I" : "");
                                })
                                .style("display", function(d) { return d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update" || d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? null : "none"; });

                            thisNode.append("rect")
                                .attr("width", nodeW)
                                .attr("height", nodeH)
                                .attr("class", "WorkflowChart-transparentRect")
                                .call(edit_node)
                                .on("mouseover", function(d) {
                                    if(!d.isStartNode) {
                                        let resourceName = (d.unifiedJobTemplate && d.unifiedJobTemplate.name) ? d.unifiedJobTemplate.name : "";
                                        if(resourceName && resourceName.length > maxNodeTextLength) {
                                            // When the graph is initially rendered all the links come after the nodes (when you look at the dom).
                                            // SVG components are painted in order of appearance.  There is no concept of z-index, only the order.
                                            // As such, we need to move the nodes after the links so that when the tooltip renders it shows up on top
                                            // of the links and not underneath them.  I tried rendering the links before the nodes but that lead to
                                            // some weird link animation that I didn't care to try to fix.
                                            svgGroup.selectAll("g.WorkflowChart-node").each(function() {
                                                this.parentNode.appendChild(this);
                                            });
                                            // After the nodes have been properly placed after the links, we need to make sure that the node that
                                            // the user is hovering over is at the very end of the list.  This way the tooltip will appear on top
                                            // of all other nodes.
                                            svgGroup.selectAll("g.WorkflowChart-node").sort(function (a) {
                                                return (a.id !== d.id) ? -1 : 1;
                                            });
                                            // Render the tooltip quickly in the dom and then remove.  This lets us know how big the tooltip is so that we can place
                                            // it properly on the workflow
                                            let tooltipDimensionChecker = $("<div style='visibility:hidden;font-size:12px;position:absolute;' class='WorkflowChart-tooltipContents'><span>" + $filter('sanitize')(resourceName) + "</span></div>");
                                            $('body').append(tooltipDimensionChecker);
                                            let tipWidth = $(tooltipDimensionChecker).outerWidth();
                                            let tipHeight = $(tooltipDimensionChecker).outerHeight();
                                            $(tooltipDimensionChecker).remove();

                                            thisNode.append("foreignObject")
                                                .attr("x", (nodeW / 2) - (tipWidth / 2))
                                                .attr("y", (tipHeight + 15) * -1)
                                                .attr("width", tipWidth)
                                                .attr("height", tipHeight+20)
                                                .attr("class", "WorkflowChart-tooltip")
                                                .html(function(){
                                                    return "<div class='WorkflowChart-tooltipContents'><span>" + $filter('sanitize')(resourceName) + "</span></div><div class='WorkflowChart-tooltipArrow'></div>";
                                                });
                                        }
                                        d3.select("#node-" + d.id)
                                            .classed("WorkflowChart-nodeHovering", true);
                                    }
                                })
                                .on("mouseout", function(d){
                                    $('.WorkflowChart-tooltip').remove();
                                    if(!d.isStartNode) {
                                        d3.select("#node-" + d.id)
                                            .classed("WorkflowChart-nodeHovering", false);
                                    }
                                });
                            thisNode.append("text")
                                .attr("x", nodeW - 45)
                                .attr("y", nodeH - 10)
                                .attr("dy", ".35em")
                                .attr("class", "WorkflowChart-detailsLink")
                                .style("display", function(d){ return d.job && d.job.status && d.job.id ? null : "none"; })
                                .text(function () {
                                    return TemplatesStrings.get('workflow_maker.DETAILS');
                                })
                                .call(details);
                            thisNode.append("circle")
                                .attr("id", function(d){return "node-" + d.id + "-add";})
                                .attr("cx", nodeW)
                                .attr("r", 10)
                                .attr("class", "WorkflowChart-addCircle WorkflowChart-nodeAddCircle")
                                .style("display", function(d) { return d.placeholder || !(userCanAddEdit) ? "none" : null; })
                                .call(add_node)
                                .on("mouseover", function(d) {
                                    d3.select("#node-" + d.id)
                                        .classed("WorkflowChart-nodeHovering", true);
                                    d3.select("#node-" + d.id + "-add")
                                        .classed("WorkflowChart-addHovering", true);
                                })
                                .on("mouseout", function(d){
                                    d3.select("#node-" + d.id)
                                        .classed("WorkflowChart-nodeHovering", false);
                                    d3.select("#node-" + d.id + "-add")
                                        .classed("WorkflowChart-addHovering", false);
                                });
                            thisNode.append("path")
                                .attr("class", "WorkflowChart-nodeAddIcon")
                                .style("fill", "white")
                                .attr("transform", function() { return "translate(" + nodeW + "," + 0 + ")"; })
                                .attr("d", d3.svg.symbol()
                                    .size(60)
                                    .type("cross")
                                )
                                .style("display", function(d) { return d.placeholder || !(userCanAddEdit) ? "none" : null; })
                                .call(add_node)
                                .on("mouseover", function(d) {
                                    d3.select("#node-" + d.id)
                                        .classed("WorkflowChart-nodeHovering", true);
                                    d3.select("#node-" + d.id + "-add")
                                        .classed("WorkflowChart-addHovering", true);
                                })
                                .on("mouseout", function(d){
                                    d3.select("#node-" + d.id)
                                        .classed("WorkflowChart-nodeHovering", false);
                                    d3.select("#node-" + d.id + "-add")
                                        .classed("WorkflowChart-addHovering", false);
                                });
                            thisNode.append("circle")
                                .attr("id", function(d){return "node-" + d.id + "-remove";})
                                .attr("cx", nodeW)
                                .attr("cy", nodeH)
                                .attr("r", 10)
                                .attr("class", "WorkflowChart-nodeRemoveCircle")
                                .style("display", function(d) { return (d.canDelete === false || d.placeholder || !(userCanAddEdit)) ? "none" : null; })
                                .call(remove_node)
                                .on("mouseover", function(d) {
                                    d3.select("#node-" + d.id)
                                        .classed("WorkflowChart-nodeHovering", true);
                                    d3.select("#node-" + d.id + "-remove")
                                        .classed("removeHovering", true);
                                })
                                .on("mouseout", function(d){
                                    d3.select("#node-" + d.id)
                                        .classed("WorkflowChart-nodeHovering", false);
                                    d3.select("#node-" + d.id + "-remove")
                                        .classed("removeHovering", false);
                                });
                            thisNode.append("path")
                                .attr("class", "WorkflowChart-nodeRemoveIcon")
                                .style("fill", "white")
                                .attr("transform", function() { return "translate(" + nodeW + "," + nodeH + ") rotate(-45)"; })
                                .attr("d", d3.svg.symbol()
                                    .size(60)
                                    .type("cross")
                                )
                                .style("display", function(d) { return (d.canDelete === false || d.placeholder || !(userCanAddEdit)) ? "none" : null; })
                                .call(remove_node)
                                .on("mouseover", function(d) {
                                    d3.select("#node-" + d.id)
                                        .classed("WorkflowChart-nodeHovering", true);
                                    d3.select("#node-" + d.id + "-remove")
                                        .classed("removeHovering", true);
                                })
                                .on("mouseout", function(d){
                                    d3.select("#node-" + d.id)
                                        .classed("WorkflowChart-nodeHovering", false);
                                    d3.select("#node-" + d.id + "-remove")
                                        .classed("removeHovering", false);
                                });

                            thisNode.append("circle")
                                .attr("class", function(d) {

                                    let statusClass = "WorkflowChart-nodeStatus ";

                                    if(d.job){
                                        switch(d.job.status) {
                                            case "pending":
                                                statusClass += "WorkflowChart-nodeStatus--running";
                                                break;
                                            case "waiting":
                                                statusClass += "WorkflowChart-nodeStatus--running";
                                                break;
                                            case "running":
                                                statusClass += "WorkflowChart-nodeStatus--running";
                                                break;
                                            case "successful":
                                                statusClass += "WorkflowChart-nodeStatus--success";
                                                break;
                                            case "failed":
                                                statusClass += "WorkflowChart-nodeStatus--failed";
                                                break;
                                            case "error":
                                                statusClass += "WorkflowChart-nodeStatus--failed";
                                                break;
                                            case "canceled":
                                                statusClass += "WorkflowChart-nodeStatus--canceled";
                                                break;
                                        }
                                    }

                                    return statusClass;
                                })
                                .style("display", function(d) { return d.job && d.job.status ? null : "none"; })
                                .attr("cy", 10)
                                .attr("cx", 10)
                                .attr("r", 6);

                            thisNode.append("foreignObject")
                                 .attr("x", 5)
                                 .attr("y", 43)
                                 .style("font-size","0.7em")
                                 .attr("class", "WorkflowChart-elapsed")
                                 .html(function (d) {
                                     if(d.job && d.job.elapsed) {
                                         let elapsedMs = d.job.elapsed * 1000;
                                         let elapsedMoment = moment.duration(elapsedMs);
                                         let paddedElapsedMoment = Math.floor(elapsedMoment.asHours()) < 10 ? "0" + Math.floor(elapsedMoment.asHours()) : Math.floor(elapsedMoment.asHours());
                                         let elapsedString = paddedElapsedMoment + moment.utc(elapsedMs).format(":mm:ss");
                                         return "<div class=\"WorkflowChart-elapsedHolder\"><span>" + elapsedString + "</span></div>";
                                     }
                                     else {
                                         return "";
                                     }
                                 })
                                 .style("display", function(d) { return (d.job && d.job.elapsed) ? null : "none"; });
                        }
                    });

                    node.exit().remove();

                    if(nodes && nodes.length > 1 && !graphLoaded) {
                        zoomToFitChart();
                    }

                    graphLoaded = true;

                    let link = svgGroup.selectAll("g.WorkflowChart-link")
                        .data(links, function(d) {
                            return d.source.id + "-" + d.target.id;
                        });

                    let linkEnter = link.enter().append("g")
                         .attr("class", "WorkflowChart-link")
                         .attr("id", function(d){return "link-" + d.source.id + "-" + d.target.id;});

                     linkEnter.append("polygon", "g")
                          .attr("class", function(d) {
                              let linkClasses = ["WorkflowChart-linkOverlay"];
                              if (d.source.isLinkEditParent && d.target.isLinkEditChild) {
                                  linkClasses.push("WorkflowChart-link--active");
                              }
                              return linkClasses.join(' ');
                          })
                          .attr("id", function(d){return "link-" + d.source.id + "-" + d.target.id + "-overlay";})
                          .attr("points",function(d) {
                              let x1 = d.source.y + nodeW;
                              let y1 = d.source.x + nodeH / 2;
                              let x2 = d.target.y;
                              let y2 = d.target.x + nodeH / 2;
                              let slope = (y2 - y1)/(x2-x1);
                              let yIntercept = y1 - slope*x1;
                              let orthogonalDistance = 8;

                              const pt1 = [x1, slope*x1 + yIntercept + orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                              const pt2 = [x2, slope*x2 + yIntercept + orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                              const pt3 = [x2, slope*x2 + yIntercept - orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                              const pt4 = [x1, slope*x1 + yIntercept - orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");

                              return [pt1, pt2, pt3, pt4].join(" ");
                          })
                          .call(edit_link)
                          .on("mouseover", function(d) {
                              if(!d.source.isStartNode && !d.source.placeholder && !d.target.placeholder && scope.mode !== 'details') {
                                  d3.select("#link-" + d.source.id + "-" + d.target.id)
                                      .classed("WorkflowChart-linkHovering", true);

                                  let xPos, yPos, arrowClass;
                                  if (d.source.x === d.target.x) {
                                      xPos = d.source.y + nodeW + ((d.target.y - (d.source.y + nodeW))/2) - (100/2);
                                      yPos = (d.source.x + nodeH/2 - d.target.x + nodeH/2)/2 + (d.target.x + nodeH/2) - 100;
                                      arrowClass = 'WorkflowChart-tooltipArrow--down';
                                  } else {
                                      xPos = d.source.y + nodeW + ((d.target.y - (d.source.y + nodeW))/2) - 115;
                                      yPos = (d.source.x + nodeH/2 - d.target.x + nodeH/2)/2 + (d.target.x + nodeH/2) - 50;
                                      arrowClass = 'WorkflowChart-tooltipArrow--right';
                                  }

                                  let edgeTypeLabel;

                                  switch(d.target.edgeType) {
                                      case "always":
                                          edgeTypeLabel = TemplatesStrings.get('workflow_maker.ALWAYS');
                                          break;
                                      case "success":
                                          edgeTypeLabel = TemplatesStrings.get('workflow_maker.ON_SUCCESS');
                                          break;
                                      case "failure":
                                          edgeTypeLabel = TemplatesStrings.get('workflow_maker.ON_FAILURE');
                                          break;
                                  }

                                  let linkInstructionText = _.get(scope, 'workflowJobTemplateObj.summary_fields.user_capabilities.edit') ? TemplatesStrings.get('workflow_maker.EDIT_LINK_TOOLTIP') : TemplatesStrings.get('workflow_maker.VIEW_LINK_TOOLTIP');

                                  linkEnter.append("foreignObject")
                                      .attr("x", xPos)
                                      .attr("y", yPos)
                                      .attr("width", 100)
                                      .attr("height", 60)
                                      .attr("class", "WorkflowChart-tooltip")
                                      .html(function(){
                                          return `<div class='WorkflowChart-tooltipContents'><div>${TemplatesStrings.get('workflow_maker.RUN')}: ${edgeTypeLabel}</div><div>${linkInstructionText}</div></div><div class='${arrowClass}'></div>`;
                                      });
                              }

                          })
                          .on("mouseout", function(d){
                              if(!d.source.isStartNode && !d.target.placeholder && scope.mode !== 'details') {
                                  d3.select("#link-" + d.source.id + "-" + d.target.id)
                                      .classed("WorkflowChart-linkHovering", false);
                              }
                              $('.WorkflowChart-tooltip').remove();
                          });

                    // Add entering links in the parent’s old position.
                    linkEnter.append("path", "g")
                         .attr("class", function(d) {
                             return (d.source.placeholder || d.target.placeholder) ? "WorkflowChart-linkPath WorkflowChart-placeholder" : "WorkflowChart-linkPath";
                         })
                         .attr("d", lineData)
                         .call(edit_link)
                         .on("mouseenter", function(d) {
                             if(!d.source.isStartNode && !d.source.placeholder && !d.target.placeholder && scope.mode !== 'details') {
                                 d3.select("#link-" + d.source.id + "-" + d.target.id)
                                     .classed("WorkflowChart-linkHovering", true);

                                 let xPos, yPos, arrowClass;
                                 if (d.source.x === d.target.x) {
                                     xPos = d.source.y + nodeW + ((d.target.y - (d.source.y + nodeW))/2) - (100/2);
                                     yPos = (d.source.x + nodeH/2 - d.target.x + nodeH/2)/2 + (d.target.x + nodeH/2) - 100;
                                     arrowClass = 'WorkflowChart-tooltipArrow--down';
                                 } else {
                                     xPos = d.source.y + nodeW + ((d.target.y - (d.source.y + nodeW))/2) - 115;
                                     yPos = (d.source.x + nodeH/2 - d.target.x + nodeH/2)/2 + (d.target.x + nodeH/2) - 50;
                                     arrowClass = 'WorkflowChart-tooltipArrow--right';
                                 }

                                 let edgeTypeLabel;

                                 switch(d.target.edgeType) {
                                     case "always":
                                         edgeTypeLabel = TemplatesStrings.get('workflow_maker.ALWAYS');
                                         break;
                                     case "success":
                                         edgeTypeLabel = TemplatesStrings.get('workflow_maker.ON_SUCCESS');
                                         break;
                                     case "failure":
                                         edgeTypeLabel = TemplatesStrings.get('workflow_maker.ON_FAILURE');
                                         break;
                                 }

                                 let linkInstructionText = _.get(scope, 'workflowJobTemplateObj.summary_fields.user_capabilities.edit') ? TemplatesStrings.get('workflow_maker.EDIT_LINK_TOOLTIP') : TemplatesStrings.get('workflow_maker.VIEW_LINK_TOOLTIP');

                                 linkEnter.append("foreignObject")
                                     .attr("x", xPos)
                                     .attr("y", yPos)
                                     .attr("width", 100)
                                     .attr("height", 60)
                                     .attr("class", "WorkflowChart-tooltip")
                                     .html(function(){
                                         return `<div class='WorkflowChart-tooltipContents'><div>${TemplatesStrings.get('workflow_maker.RUN')}: ${edgeTypeLabel}</div><div>${linkInstructionText}</div></div><div class='${arrowClass}'></div>`;
                                     });
                             }
                         })
                         .on("mouseleave", function(d){
                             if(!d.source.isStartNode && !d.target.placeholder && scope.mode !== 'details') {
                                 d3.select("#link-" + d.source.id + "-" + d.target.id)
                                     .classed("WorkflowChart-linkHovering", false);
                             }
                             $('.WorkflowChart-tooltip').remove();
                         })
                         .attr('stroke', function(d) {
                             if(d.target.edgeType) {
                                 if(d.target.edgeType === "failure") {
                                     return "#d9534f";
                                 }
                                 else if(d.target.edgeType === "success") {
                                     return "#5cb85c";
                                 }
                                 else if(d.target.edgeType === "always"){
                                     return "#337ab7";
                                 }
                             }
                             else {
                                 return "#D7D7D7";
                             }
                         });

                    linkEnter.append("circle")
                         .attr("id", function(d){return "link-" + d.source.id + "-" + d.target.id + "-add";})
                         .attr("cx", function(d) {
                             return (d.source.isStartNode) ? (d.target.y + d.source.y + rootW) / 2 : (d.target.y + d.source.y + nodeW) / 2;
                         })
                         .attr("cy", function(d) {
                             return (d.source.isStartNode) ? ((d.target.x + startNodeOffsetY + rootH/2) + (d.source.x + nodeH/2)) / 2 : (d.target.x + d.source.x + nodeH) / 2;
                         })
                         .attr("r", 10)
                         .attr("class", "WorkflowChart-addCircle WorkflowChart-circleBetweenNodes")
                         .style("display", function(d) { return (d.source.placeholder || d.target.placeholder || !(userCanAddEdit)) ? "none" : null; })
                         .call(add_node_between)
                         .on("mouseover", function(d) {
                             d3.select("#link-" + d.source.id + "-" + d.target.id)
                                 .classed("WorkflowChart-addHovering", true);
                         })
                         .on("mouseout", function(d){
                             d3.select("#link-" + d.source.id + "-" + d.target.id)
                                 .classed("WorkflowChart-addHovering", false);
                         });

                    linkEnter.append("path")
                         .attr("class", "WorkflowChart-betweenNodesIcon")
                         .style("fill", "white")
                         .attr("transform", function(d) {
                             let translate;
                             if(d.source.isStartNode) {
                                 translate = "translate(" + (d.target.y + d.source.y + rootW) / 2 + "," + ((d.target.x + startNodeOffsetY + rootH/2) + (d.source.x + nodeH/2)) / 2 + ")";
                             }
                             else {
                                 translate = "translate(" + (d.target.y + d.source.y + nodeW) / 2 + "," + (d.target.x + d.source.x + nodeH) / 2 + ")";
                             }
                             return translate;
                         })
                         .attr("d", d3.svg.symbol()
                             .size(60)
                             .type("cross")
                         )
                         .style("display", function(d) { return (d.source.placeholder || d.target.placeholder || !(userCanAddEdit)) ? "none" : null; })
                         .call(add_node_between)
                         .on("mouseover", function(d) {
                             d3.select("#link-" + d.source.id + "-" + d.target.id)
                                 .classed("WorkflowChart-addHovering", true);
                         })
                         .on("mouseout", function(d){
                             d3.select("#link-" + d.source.id + "-" + d.target.id)
                                 .classed("WorkflowChart-addHovering", false);
                         });

                    link.exit().remove();

                    // Transition nodes and links to their new positions.
                    let t = baseSvg.transition();

                    t.selectAll(".WorkflowChart-nodeAddCircle")
                        .style("display", function(d) { return d.placeholder || !(userCanAddEdit) ? "none" : null; });

                    t.selectAll(".WorkflowChart-nodeAddIcon")
                        .style("display", function(d) { return d.placeholder || !(userCanAddEdit) ? "none" : null; });

                    t.selectAll(".WorkflowChart-nodeRemoveCircle")
                        .style("display", function(d) { return (d.canDelete === false || d.placeholder || !(userCanAddEdit)) ? "none" : null; });

                    t.selectAll(".WorkflowChart-nodeRemoveIcon")
                        .style("display", function(d) { return (d.canDelete === false || d.placeholder || !(userCanAddEdit)) ? "none" : null; });

                    t.selectAll(".WorkflowChart-linkPath")
                            .attr("class", function(d) {
                                return (d.source.placeholder || d.target.placeholder) ? "WorkflowChart-linkPath WorkflowChart-placeholder" : "WorkflowChart-linkPath";
                            })
                            .attr("d", lineData)
                            .attr('stroke', function(d) {
                                if(d.target.edgeType) {
                                    if(d.target.edgeType === "failure") {
                                        return "#d9534f";
                                    }
                                    else if(d.target.edgeType === "success") {
                                        return "#5cb85c";
                                    }
                                    else if(d.target.edgeType === "always"){
                                        return "#337ab7";
                                    }
                                }
                                else {
                                    return "#D7D7D7";
                                }
                            });

                    t.selectAll(".WorkflowChart-circleBetweenNodes")
                        .style("display", function(d) { return (d.source.placeholder || d.target.placeholder || !(userCanAddEdit)) ? "none" : null; })
                        .attr("cx", function(d) {
                            return (d.source.isStartNode) ? (d.target.y + d.source.y + rootW) / 2 : (d.target.y + d.source.y + nodeW) / 2;
                        })
                        .attr("cy", function(d) {
                            return (d.source.isStartNode) ? ((d.target.x + startNodeOffsetY + rootH/2) + (d.source.x + nodeH/2)) / 2 : (d.target.x + d.source.x + nodeH) / 2;
                        });

                    t.selectAll(".WorkflowChart-linkOverlay")
                        .attr("class", function(d) {
                            let linkClasses = ["WorkflowChart-linkOverlay"];
                            if (d.source.isLinkEditParent && d.target.isLinkEditChild) {
                                linkClasses.push("WorkflowChart-link--active");
                            }
                            return linkClasses.join(' ');
                        })
                        .attr("points",function(d) {
                            let x1 = d.source.y + nodeW;
                            let y1 = d.source.x + nodeH / 2;
                            let x2 = d.target.y;
                            let y2 = d.target.x + nodeH / 2;
                            let slope = (y2 - y1)/(x2-x1);
                            let yIntercept = y1 - slope*x1;
                            let orthogonalDistance = 8;

                            const pt1 = [x1, slope*x1 + yIntercept + orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                            const pt2 = [x2, slope*x2 + yIntercept + orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                            const pt3 = [x2, slope*x2 + yIntercept - orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                            const pt4 = [x1, slope*x1 + yIntercept - orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");

                            return [pt1, pt2, pt3, pt4].join(" ");
                        });

                    t.selectAll(".WorkflowChart-betweenNodesIcon")
                        .style("display", function(d) { return (d.source.placeholder || d.target.placeholder || !(userCanAddEdit)) ? "none" : null; })
                        .attr("transform", function(d) {
                            let translate;
                            if(d.source.isStartNode) {
                                translate = "translate(" + (d.target.y + d.source.y + rootW) / 2 + "," + ((d.target.x + startNodeOffsetY + rootH/2) + (d.source.x + nodeH/2)) / 2 + ")";
                            }
                            else {
                                translate = "translate(" + (d.target.y + d.source.y + nodeW) / 2 + "," + (d.target.x + d.source.x + nodeH) / 2 + ")";
                            }
                            return translate;
                        });

                    t.selectAll(".WorkflowChart-rect")
                        .attr('stroke', function(d) {
                            if(d.job && d.job.status) {
                                if(d.job.status === "successful"){
                                    return "#5cb85c";
                                }
                                else if (d.job.status === "failed" || d.job.status === "error" || d.job.status === "cancelled") {
                                    return "#d9534f";
                                }
                                else {
                                    return "#D7D7D7";
                                }
                            }
                            else {
                                return "#D7D7D7";
                            }
                         })
                         .attr("class", function(d) {
                             let classString = d.placeholder ? "WorkflowChart-rect WorkflowChart-placeholder" : "WorkflowChart-rect";
                             classString += !d.unifiedJobTemplate ? " WorkflowChart-dashedNode" : "";
                             return classString;
                         });

                    t.selectAll(".WorkflowChart-node")
                        .attr("parent", function(d){return d.parent ? d.parent.id : null;})
                        .attr("transform", function(d) {d.px = d.x; d.py = d.y; return "translate(" + d.y + "," + d.x + ")"; });

                    t.selectAll(".WorkflowChart-nodeTypeCircle")
                        .style("display", function(d) { return d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update" || d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update" ) ? null : "none"; });

                    t.selectAll(".WorkflowChart-nodeTypeLetter")
                        .text(function (d) {
                            return (d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update")) ? "P" : (d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? "I" : "");
                        })
                        .style("display", function(d) { return d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update" || d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? null : "none"; });

                    t.selectAll(".WorkflowChart-nodeStatus")
                        .attr("class", function(d) {

                            let statusClass = "WorkflowChart-nodeStatus ";

                            if(d.job){
                                switch(d.job.status) {
                                    case "pending":
                                        statusClass += "WorkflowChart-nodeStatus--running";
                                        break;
                                    case "waiting":
                                        statusClass += "WorkflowChart-nodeStatus--running";
                                        break;
                                    case "running":
                                        statusClass += "WorkflowChart-nodeStatus--running";
                                        break;
                                    case "successful":
                                        statusClass += "WorkflowChart-nodeStatus--success";
                                        break;
                                    case "failed":
                                        statusClass += "WorkflowChart-nodeStatus--failed";
                                        break;
                                    case "error":
                                        statusClass += "WorkflowChart-nodeStatus--failed";
                                        break;
                                    case "canceled":
                                        statusClass += "WorkflowChart-nodeStatus--canceled";
                                        break;
                                }
                            }

                            return statusClass;
                        })
                        .style("display", function(d) { return d.job && d.job.status ? null : "none"; })
                        .transition()
                        .duration(0)
                        .attr("r", 6)
                        .each(function(d) {
                            if(d.job && d.job.status && (d.job.status === "pending" || d.job.status === "waiting" || d.job.status === "running")) {
                                // Pulse the circle
                                var circle = d3.select(this);
                    			(function repeat() {
                    				circle = circle.transition()
                    					.duration(2000)
                    					.attr("r", 6)
                    					.transition()
                    					.duration(2000)
                    					.attr("r", 0)
                    					.ease('sine')
                    					.each("end", repeat);
                    			})();
                            }
                        });

                    t.selectAll(".WorkflowChart-nameText")
                        .attr("x", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? 20 : nodeW / 2; })
                        .attr("y", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? 10 : nodeH / 2; })
                        .attr("text-anchor", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? "inherit" : "middle"; })
                        .text(function (d) {
                            return (d.unifiedJobTemplate && d.unifiedJobTemplate.name) ? wrap(d.unifiedJobTemplate.name) : "";
                        });

                    t.selectAll(".WorkflowChart-detailsLink")
                        .style("display", function(d){ return d.job && d.job.status && d.job.id ? null : "none"; });

                    t.selectAll(".WorkflowChart-deletedText")
                        .style("display", function(d){ return d.unifiedJobTemplate || d.placeholder ? "none" : null; });

                    t.selectAll(".WorkflowChart-activeNode")
                        .style("display", function(d) { return d.isActiveEdit ? null : "none"; });

                    t.selectAll(".WorkflowChart-elapsed")
                        .style("display", function(d) { return (d.job && d.job.elapsed) ? null : "none"; });
                }
                else if(!scope.watchDimensionsSet){
                    scope.watchDimensionsSet = scope.$watch('dimensionsSet', function(){
                        if(scope.dimensionsSet) {
                            scope.watchDimensionsSet();
                            scope.watchDimensionsSet = null;
                            update();
                        }
                    });
                }
            }

            function add_node() {
                this.on("click", function(d) {
                    if((scope.workflowJobTemplateObj && scope.workflowJobTemplateObj.summary_fields && scope.workflowJobTemplateObj.summary_fields.user_capabilities && scope.workflowJobTemplateObj.summary_fields.user_capabilities.edit) || scope.canAddWorkflowJobTemplate) {
                        scope.addNode({
                            parent: d,
                            betweenTwoNodes: false
                        });
                    }
                });
            }

            function add_node_between() {
                this.on("click", function(d) {
                    if((scope.workflowJobTemplateObj && scope.workflowJobTemplateObj.summary_fields && scope.workflowJobTemplateObj.summary_fields.user_capabilities && scope.workflowJobTemplateObj.summary_fields.user_capabilities.edit) || scope.canAddWorkflowJobTemplate) {
                        scope.addNode({
                            parent: d,
                            betweenTwoNodes: true
                        });
                    }
                });
            }

            function remove_node() {
                this.on("click", function(d) {
                    if((scope.workflowJobTemplateObj && scope.workflowJobTemplateObj.summary_fields && scope.workflowJobTemplateObj.summary_fields.user_capabilities && scope.workflowJobTemplateObj.summary_fields.user_capabilities.edit) || scope.canAddWorkflowJobTemplate) {
                        scope.deleteNode({
                            nodeToDelete: d
                        });
                    }
                });
            }

            function edit_node() {
                this.on("click", function(d) {
                    if(d.canEdit){
                        scope.editNode({
                            nodeToEdit: d
                        });
                    }
                });
            }

            function edit_link() {
                this.on("click", function(d) {
                    if(!d.source.isStartNode && !d.source.placeholder && !d.target.placeholder && scope.mode !== 'details'){
                        scope.editLink({
                            parentId: d.source.id,
                            childId: d.target.id
                        });
                    }
                });
            }

            function link_node() {
                this.on("click", function(d) {
                    alert('this does not work, don\'t click it');
                });
            }

            function details() {
                this.on("mouseover", function() {
                    d3.select(this).style("text-decoration", "underline");
                });
                this.on("mouseout", function() {
                    d3.select(this).style("text-decoration", null);
                });
                this.on("click", function(d) {

                    let goToJobResults = function(job_type) {
                        if(job_type === 'job') {
                            $state.go('output', {id: d.job.id, type: 'playbook'});
                        }
                        else if(job_type === 'inventory_update') {
                            $state.go('output', {id: d.job.id, type: 'inventory'});
                        }
                        else if(job_type === 'project_update') {
                            $state.go('output', {id: d.job.id, type: 'project'});
                        }
                    };

                    if(d.job.id) {
                        if(d.unifiedJobTemplate) {
                            goToJobResults(d.unifiedJobTemplate.unified_job_type);
                        }
                        else {
                            // We don't have access to the unified resource and have to make
                            // a GET request in order to find out what type job this was
                            // so that we can route the user to the correct stdout view

                            Rest.setUrl(GetBasePath("unified_jobs") + "?id=" + d.job.id);
                            Rest.get()
                            .then(function (res) {
                                if(res.data.results && res.data.results.length > 0) {
                                    goToJobResults(res.data.results[0].type);
                                }
                            })
                            .catch(({data, status}) => {
                                ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Unable to get job: ' + status });
                            });
                        }
                    }
                });
            }

            scope.$watch('canAddWorkflowJobTemplate', function() {
                // Redraw the graph if permissions change
                if(scope.treeData) {
                    update();
                }
            });

            scope.$on('refreshWorkflowChart', function(){
                if(scope.treeData) {
                    update();
                }
            });

            scope.$on('panWorkflowChart', function(evt, params) {
                manualPan(params.direction);
            });

            scope.$on('resetWorkflowChart', function(){
                resetZoomAndPan();
            });

            scope.$on('zoomWorkflowChart', function(evt, params) {
                manualZoom(params.zoom);
            });

            scope.$on('zoomToFitChart', function() {
                zoomToFitChart();
            });

            let clearWatchTreeData = scope.$watch('treeData', function(newVal) {
                if(newVal) {
                    update();
                    clearWatchTreeData();
                }
            });

            function onResize(){
                let dimensions = calcAvailableScreenSpace();

                $('.WorkflowMaker-chart').css("width", dimensions.width);
                $('.WorkflowMaker-chart').css("height", dimensions.height);
            }

            function cleanUpResize() {
                angular.element($window).off('resize', onResize);
            }

            if(scope.mode === 'details') {
                angular.element($window).on('resize', onResize);
                scope.$on('$destroy', cleanUpResize);

                scope.$on('workflowDetailsResized', function(){
                    $('.WorkflowMaker-chart').hide();
                    $timeout(function(){
                        onResize();
                        $('.WorkflowMaker-chart').show();
                    });
                });
            }
            else {
                scope.$on('workflowMakerModalResized', function(){
                    let dimensions = calcAvailableScreenSpace();

                    $('.WorkflowMaker-chart').css("width", dimensions.width);
                    $('.WorkflowMaker-chart').css("height", dimensions.height);
                });
            }
        }
    };
}];
