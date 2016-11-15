/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    function() {

    return {
        scope: {
            treeData: '=',
            canAddWorkflowJobTemplate: '=',
            addNode: '&',
            editNode: '&',
            deleteNode: '&'
        },
        restrict: 'E',
        link: function(scope, element) {

            scope.$watch('canAddWorkflowJobTemplate', function() {
                // Redraw the graph if permissions change
                update();
            });

            let margin = {top: 20, right: 20, bottom: 20, left: 20},
                width = 950,
                height = 590 - margin.top - margin.bottom,
                i = 0,
                rectW = 120,
                rectH = 60,
                rootW = 60,
                rootH = 40;

            let tree = d3.layout.tree()
                    .size([height, width]);

            let line = d3.svg.line()
                     .x(function(d){return d.x;})
                     .y(function(d){return d.y;});

            function lineData(d){

                let sourceX = d.source.isStartNode ? d.source.y + rootW : d.source.y + rectW;
                let sourceY = d.source.isStartNode ? d.source.x + 10 + rootH / 2 : d.source.x + rectH / 2;
                let targetX = d.target.y;
                let targetY = d.target.x + rectH / 2;

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
                if(text && text.length > 15) {
                    return text.substring(0,15) + '...';
                }
                else {
                    return text;
                }
            }

            let svg = d3.select(element[0]).append("svg")
                    .attr("width", width)
                    .attr("height", height)
                    .attr("class", "WorkflowChart-svg")
                    .append("g")
                    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            let node = svg.selectAll(".node"),
                link = svg.selectAll(".link");

            function update() {
                // Declare the nodes
                let nodes = tree.nodes(scope.treeData);
                node = node.data(nodes, function(d) { d.y = d.depth * 180; return d.id || (d.id = ++i); });
                link = link.data(tree.links(nodes), function(d) { return d.source.id + "-" + d.target.id; });

                let nodeEnter = node.enter().append("g")
                        .attr("class", "node")
                        .attr("id", function(d){return "node-" + d.id;})
                        .attr("parent", function(d){return d.parent ? d.parent.id : null;})
                        .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; })
                        .attr("fill", "red");

                nodeEnter.each(function(d) {
                    let thisNode = d3.select(this);
                    if(d.isStartNode) {
                        thisNode.append("rect")
                            .attr("width", 60)
                            .attr("height", 40)
                            .attr("y", 10)
                            .attr("rx", 5)
                            .attr("ry", 5)
                            .attr("fill", "#5cb85c")
                            .attr("class", "WorkflowChart-rootNode")
                            .call(add_node);
                        thisNode.append("path")
                            .style("fill", "white")
                            .attr("transform", function() { return "translate(" + 30 + "," + 30 + ")"; })
                            .attr("d", d3.svg.symbol()
                                .size(120)
                                .type("cross")
                            )
                            .call(add_node);
                        thisNode.append("text")
                            .attr("x", 14)
                            .attr("y", 0)
                            .attr("dy", ".35em")
                            .attr("class", "WorkflowChart-defaultText")
                            .text(function () { return "START"; });
                    }
                    else {
                        thisNode.append("rect")
                            .attr("width", rectW)
                            .attr("height", rectH)
                            .attr("rx", 5)
                            .attr("ry", 5)
                            .attr('stroke', function(d) { return d.isActiveEdit ? "#337ab7" : "#D7D7D7"; })
                            .attr('stroke-width', function(d){ return d.isActiveEdit ? "2px" : "1px"; })
                            .attr("class", function(d) {
                                return d.placeholder ? "rect placeholder" : "rect";
                            });
                        thisNode.append("text")
                            .attr("x", rectW / 2)
                            .attr("y", rectH / 2)
                            .attr("dy", ".35em")
                            .attr("text-anchor", "middle")
                            .attr("class", "WorkflowChart-defaultText WorkflowChart-nameText")
                            .text(function (d) {
                                return (d.unifiedJobTemplate && d.unifiedJobTemplate.name) ? d.unifiedJobTemplate.name : "";
                            }).each(wrap);

                        thisNode.append("circle")
                            .attr("cy", rectH)
                            .attr("r", 10)
                            .attr("class", "WorkflowChart-nodeTypeCircle")
                            .style("display", function(d) { return d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update" || d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? null : "none"; });

                        thisNode.append("text")
                            .attr("y", rectH)
                            .attr("dy", ".35em")
                            .attr("text-anchor", "middle")
                            .attr("class", "WorkflowChart-nodeTypeLetter")
                            .text(function (d) {
                                return (d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update")) ? "P" : (d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? "I" : "");
                            })
                            .style("display", function(d) { return d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update" || d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? null : "none"; });

                        thisNode.append("rect")
                            .attr("width", rectW)
                            .attr("height", rectH)
                            .attr("class", "transparentRect")
                            .call(edit_node)
                            .on("mouseover", function(d) {
                                if(!d.isStartNode) {
                                    d3.select("#node-" + d.id)
                                        .classed("hovering", true);
                                }
                            })
                            .on("mouseout", function(d){
                                if(!d.isStartNode) {
                                    d3.select("#node-" + d.id)
                                        .classed("hovering", false);
                                }
                            });
                        thisNode.append("circle")
                            .attr("id", function(d){return "node-" + d.id + "-add";})
                            .attr("cx", rectW)
                            .attr("r", 10)
                            .attr("class", "addCircle nodeCircle")
                            .style("display", function(d) { return d.placeholder || scope.canAddWorkflowJobTemplate === false ? "none" : null; })
                            .call(add_node)
                            .on("mouseover", function(d) {
                                d3.select("#node-" + d.id)
                                    .classed("hovering", true);
                                d3.select("#node-" + d.id + "-add")
                                    .classed("addHovering", true);
                            })
                            .on("mouseout", function(d){
                                d3.select("#node-" + d.id)
                                    .classed("hovering", false);
                                d3.select("#node-" + d.id + "-add")
                                    .classed("addHovering", false);
                            });
                        thisNode.append("path")
                            .attr("class", "nodeAddCross WorkflowChart-hoverPath")
                            .style("fill", "white")
                            .attr("transform", function() { return "translate(" + rectW + "," + 0 + ")"; })
                            .attr("d", d3.svg.symbol()
                                .size(60)
                                .type("cross")
                            )
                            .style("display", function(d) { return d.placeholder || scope.canAddWorkflowJobTemplate === false ? "none" : null; })
                            .call(add_node)
                            .on("mouseover", function(d) {
                                d3.select("#node-" + d.id)
                                    .classed("hovering", true);
                                d3.select("#node-" + d.id + "-add")
                                    .classed("addHovering", true);
                            })
                            .on("mouseout", function(d){
                                d3.select("#node-" + d.id)
                                    .classed("hovering", false);
                                d3.select("#node-" + d.id + "-add")
                                    .classed("addHovering", false);
                            });
                        thisNode.append("circle")
                            .attr("id", function(d){return "node-" + d.id + "-remove";})
                            .attr("cx", rectW)
                            .attr("cy", rectH)
                            .attr("r", 10)
                            .attr("class", "removeCircle")
                            .style("display", function(d) { return (d.canDelete === false || d.placeholder || scope.canAddWorkflowJobTemplate === false) ? "none" : null; })
                            .call(remove_node)
                            .on("mouseover", function(d) {
                                d3.select("#node-" + d.id)
                                    .classed("hovering", true);
                                d3.select("#node-" + d.id + "-remove")
                                    .classed("removeHovering", true);
                            })
                            .on("mouseout", function(d){
                                d3.select("#node-" + d.id)
                                    .classed("hovering", false);
                                d3.select("#node-" + d.id + "-remove")
                                    .classed("removeHovering", false);
                            });
                        thisNode.append("path")
                            .attr("class", "nodeRemoveCross WorkflowChart-hoverPath")
                            .style("fill", "white")
                            .attr("transform", function() { return "translate(" + rectW + "," + rectH + ") rotate(-45)"; })
                            .attr("d", d3.svg.symbol()
                                .size(60)
                                .type("cross")
                            )
                            .style("display", function(d) { return (d.canDelete === false || d.placeholder || scope.canAddWorkflowJobTemplate === false) ? "none" : null; })
                            .call(remove_node)
                            .on("mouseover", function(d) {
                                d3.select("#node-" + d.id)
                                    .classed("hovering", true);
                                d3.select("#node-" + d.id + "-remove")
                                    .classed("removeHovering", true);
                            })
                            .on("mouseout", function(d){
                                d3.select("#node-" + d.id)
                                    .classed("hovering", false);
                                d3.select("#node-" + d.id + "-remove")
                                    .classed("removeHovering", false);
                            });
                    }
                });

                node.exit().remove();

                let linkEnter = link.enter().append("g")
                    .attr("class", "nodeConnector")
                    .attr("id", function(d){return "link-" + d.source.id + "-" + d.target.id;});

                // Add entering links in the parent’s old position.
                linkEnter.insert("path", ".node")
                        .attr("class", function(d) {
                            return (d.source.placeholder || d.target.placeholder) ? "link placeholder" : "link";
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

                linkEnter.append("circle")
                    .attr("id", function(d){return "link-" + d.source.id + "-" + d.target.id + "-add";})
                    .attr("cx", function(d) {
                        return (d.target.y + d.source.y + rectW) / 2;
                    })
                    .attr("cy", function(d) {
                        return (d.target.x + d.source.x + rectH) / 2;
                    })
                    .attr("r", 10)
                    .attr("class", "addCircle linkCircle")
                    .style("display", function(d) { return (d.source.placeholder || d.target.placeholder || scope.canAddWorkflowJobTemplate === false) ? "none" : null; })
                    .call(add_node_between)
                    .on("mouseover", function(d) {
                        d3.select("#link-" + d.source.id + "-" + d.target.id)
                            .classed("hovering", true);
                        d3.select("#link-" + d.source.id + "-" + d.target.id + "-add")
                            .classed("addHovering", true);
                    })
                    .on("mouseout", function(d){
                        d3.select("#link-" + d.source.id + "-" + d.target.id)
                            .classed("hovering", false);
                        d3.select("#link-" + d.source.id + "-" + d.target.id + "-add")
                            .classed("addHovering", false);
                    });

                linkEnter.append("path")
                    .attr("class", "linkCross")
                    .style("fill", "white")
                    .attr("transform", function(d) { return "translate(" + (d.target.y + d.source.y + rectW) / 2 + "," + (d.target.x + d.source.x + rectH) / 2 + ")"; })
                    .attr("d", d3.svg.symbol()
                        .size(60)
                        .type("cross")
                    )
                    .style("display", function(d) { return (d.source.placeholder || d.target.placeholder || scope.canAddWorkflowJobTemplate === false) ? "none" : null; })
                    .call(add_node_between)
                    .on("mouseover", function(d) {
                        d3.select("#link-" + d.source.id + "-" + d.target.id)
                            .classed("hovering", true);
                        d3.select("#link-" + d.source.id + "-" + d.target.id + "-add")
                            .classed("addHovering", true);
                    })
                    .on("mouseout", function(d){
                        d3.select("#link-" + d.source.id + "-" + d.target.id)
                            .classed("hovering", false);
                        d3.select("#link-" + d.source.id + "-" + d.target.id + "-add")
                            .classed("addHovering", false);
                    });

                link.exit().remove();

                // Transition nodes and links to their new positions.
                let t = svg.transition();

                t.selectAll(".nodeCircle")
                    .style("display", function(d) { return d.placeholder || scope.canAddWorkflowJobTemplate === false ? "none" : null; });

                t.selectAll(".nodeAddCross")
                    .style("display", function(d) { return d.placeholder || scope.canAddWorkflowJobTemplate === false ? "none" : null; });

                t.selectAll(".removeCircle")
                    .style("display", function(d) { return (d.canDelete === false || d.placeholder || scope.canAddWorkflowJobTemplate === false) ? "none" : null; });

                t.selectAll(".nodeRemoveCross")
                    .style("display", function(d) { return (d.canDelete === false || d.placeholder || scope.canAddWorkflowJobTemplate === false) ? "none" : null; });

                t.selectAll(".link")
                        .attr("class", function(d) {
                            return (d.source.placeholder || d.target.placeholder) ? "link placeholder" : "link";
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

                t.selectAll(".linkCircle")
                    .style("display", function(d) { return (d.source.placeholder || d.target.placeholder) ? "none" : null; })
                    .attr("cx", function(d) {
                        return (d.target.y + d.source.y + rectW) / 2;
                    })
                    .attr("cy", function(d) {
                        return (d.target.x + d.source.x + rectH) / 2;
                    });

                t.selectAll(".linkCross")
                    .style("display", function(d) { return (d.source.placeholder || d.target.placeholder) ? "none" : null; })
                    .attr("transform", function(d) { return "translate(" + (d.target.y + d.source.y + rectW) / 2 + "," + (d.target.x + d.source.x + rectH) / 2 + ")"; });

                t.selectAll(".rect")
                    .attr('stroke', function(d) { return d.isActiveEdit ? "#337ab7" : "#D7D7D7"; })
                    .attr('stroke-width', function(d){ return d.isActiveEdit ? "2px" : "1px"; })
                    .attr("class", function(d) {
                        return d.placeholder ? "rect placeholder" : "rect";
                    });

                t.selectAll(".WorkflowChart-nameText")
                    .text(function (d) {
                        return (d.unifiedJobTemplate && d.unifiedJobTemplate.name) ? wrap(d.unifiedJobTemplate.name) : "";
                    });

                t.selectAll(".node")
                    .attr("transform", function(d) {d.px = d.x; d.py = d.y; return "translate(" + d.y + "," + d.x + ")"; });

                t.selectAll(".WorkflowChart-nodeTypeCircle")
                    .style("display", function(d) { return d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update" || d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update" ) ? null : "none"; });

                t.selectAll(".WorkflowChart-nodeTypeLetter")
                    .text(function (d) {
                        return (d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update")) ? "P" : (d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? "I" : "");
                    })
                    .style("display", function(d) { return d.unifiedJobTemplate && (d.unifiedJobTemplate.type === "project" || d.unifiedJobTemplate.unified_job_type === "project_update" || d.unifiedJobTemplate.type === "inventory_source" || d.unifiedJobTemplate.unified_job_type === "inventory_update") ? null : "none"; });

            }

            function add_node() {
                this.on("click", function(d) {
                    if(scope.canAddWorkflowJobTemplate !== false) {
                        scope.addNode({
                            parent: d,
                            betweenTwoNodes: false
                        });
                    }
                });
            }

            function add_node_between() {
                this.on("click", function(d) {
                    if(scope.canAddWorkflowJobTemplate !== false) {
                        scope.addNode({
                            parent: d,
                            betweenTwoNodes: true
                        });
                    }
                });
            }

            function remove_node() {
                this.on("click", function(d) {
                    if(scope.canAddWorkflowJobTemplate !== false) {
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

            scope.$on('refreshWorkflowChart', function(){
                update();
            });

        }
    };
}];
