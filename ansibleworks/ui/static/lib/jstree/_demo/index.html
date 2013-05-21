<!DOCTYPE html
PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<title>jsTree v.1.0 - Demo</title>
	<script type="text/javascript" src="../_lib/jquery.js"></script>
	<script type="text/javascript" src="../_lib/jquery.cookie.js"></script>
	<script type="text/javascript" src="../_lib/jquery.hotkeys.js"></script>
	<script type="text/javascript" src="../jquery.jstree.js"></script>
	<link type="text/css" rel="stylesheet" href="../_docs/syntax/!style.css"/>
	<link type="text/css" rel="stylesheet" href="../_docs/!style.css"/>
	<script type="text/javascript" src="../_docs/syntax/!script.js"></script>
</head>
<body id="demo_body">
<div id="container">

<h1 id="dhead">jsTree v.1.0</h1>
<h1>DEMO</h1>
<h2>Creating a tree, binding events, using the instance</h2>
<div id="description">
<p>Here is how you create an instance, bind an event and then get the instance.</p>
<div id="demo1" class="demo" style="height:100px;">
	<ul>
		<li id="phtml_1">
			<a href="#">Root node 1</a>
			<ul>
				<li id="phtml_2">
					<a href="#">Child node 1</a>
				</li>
				<li id="phtml_3">
					<a href="#">Child node 2</a>
				</li>
			</ul>
		</li>
		<li id="phtml_4">
			<a href="#">Root node 2</a>
		</li>
	</ul>
</div>
<script type="text/javascript" class="source below">
$(function () {
	// TO CREATE AN INSTANCE
	// select the tree container using jQuery
	$("#demo1")
		// call `.jstree` with the options object
		.jstree({
			// the `plugins` array allows you to configure the active plugins on this instance
			"plugins" : ["themes","html_data","ui","crrm","hotkeys"],
			// each plugin you have included can have its own config object
			"core" : { "initially_open" : [ "phtml_1" ] }
			// it makes sense to configure a plugin only if overriding the defaults
		})
		// EVENTS
		// each instance triggers its own events - to process those listen on the container
		// all events are in the `.jstree` namespace
		// so listen for `function_name`.`jstree` - you can function names from the docs
		.bind("loaded.jstree", function (event, data) {
			// you get two params - event & data - check the core docs for a detailed description
		});
	// INSTANCES
	// 1) you can call most functions just by selecting the container and calling `.jstree("func",`
	setTimeout(function () { $("#demo1").jstree("set_focus"); }, 500);
	// with the methods below you can call even private functions (prefixed with `_`)
	// 2) you can get the focused instance using `$.jstree._focused()`. 
	setTimeout(function () { $.jstree._focused().select_node("#phtml_1"); }, 1000);
	// 3) you can use $.jstree._reference - just pass the container, a node inside it, or a selector
	setTimeout(function () { $.jstree._reference("#phtml_1").close_node("#phtml_1"); }, 1500);
	// 4) when you are working with an event you can use a shortcut
	$("#demo1").bind("open_node.jstree", function (e, data) {
		// data.inst is the instance which triggered this event
		data.inst.select_node("#phtml_2", true);
	});
	setTimeout(function () { $.jstree._reference("#phtml_1").open_node("#phtml_1"); }, 2500);
});
</script>
</div>

<h2>Doing something when the tree is loaded</h2>
<div id="description">
<p>You can use a few events to do that.</p>
<div id="demo2" class="demo" style="height:100px;">
	<ul>
		<li id="rhtml_1" class="jstree-open">
			<a href="#">Root node 1</a>
			<ul>
				<li id="rhtml_2">
					<a href="#">Child node 1</a>
				</li>
				<li id="rhtml_3">
					<a href="#">Child node 2</a>
				</li>
			</ul>
		</li>
		<li id="rhtml_4">
			<a href="#">Root node 2</a>
		</li>
	</ul>
</div>
<script type="text/javascript" class="source below">
// Note method 2) and 3) use `one`, this is because if `refresh` is called those events are triggered
$(function () {
	$("#demo2")
		.jstree({ "plugins" : ["themes","html_data","ui"] })
		// 1) the loaded event fires as soon as data is parsed and inserted
		.bind("loaded.jstree", function (event, data) { })
		// 2) but if you are using the cookie plugin or the core `initially_open` option:
		.one("reopen.jstree", function (event, data) { })
		// 3) but if you are using the cookie plugin or the UI `initially_select` option:
		.one("reselect.jstree", function (event, data) { });
});
</script>
</div>

<h2>Doing something when a node is clicked</h2>
<div id="description">
<div id="demo3" class="demo" style="height:100px;">
	<ul>
		<li id="shtml_1" class="jstree-open">
			<a href="#">Root node 1</a>
			<ul>
				<li id="shtml_2">
					<a href="#">Child node 1</a>
				</li>
				<li id="shtml_3">
					<a href="#">Child node 2</a>
				</li>
			</ul>
		</li>
		<li id="shtml_4">
			<a href="#">Root node 2</a>
		</li>
	</ul>
</div>
<script type="text/javascript" class="source below">
$(function () {
	$("#demo3")
		.jstree({ "plugins" : ["themes","html_data","ui"] })
		// 1) if using the UI plugin bind to select_node
		.bind("select_node.jstree", function (event, data) { 
			// `data.rslt.obj` is the jquery extended node that was clicked
			alert(data.rslt.obj.attr("id"));
		})
		// 2) if not using the UI plugin - the Anchor tags work as expected
		//    so if the anchor has a HREF attirbute - the page will be changed
		//    you can actually prevent the default, etc (normal jquery usage)
		.delegate("a", "click", function (event, data) { event.preventDefault(); })
});
</script>
</div>

<h2>Using CSS to make nodes wrap</h2>
<div id="description">
<div id="demo4" class="demo" style="height:120px;">
	<ul>
		<li class="jstree-open">
			<a href="#">Root node 1</a>
			<ul>
				<li>
					<a href="#">Child node 1 with a long text which would normally just cause a scrollbar, but with this line of CSS it will actually wrap, this is not really throughly tested but it works</a>
				</li>
				<li>
					<a href="#">Child node 2</a>
				</li>
			</ul>
		</li>
		<li>
			<a href="#">Root node 2</a>
		</li>
	</ul>
</div>
<style type="text/css" class="source below">
#demo4 a { white-space:normal !important; height: auto; padding:1px 2px; } 
#demo4 li > ins { vertical-align:top; }
#demo4 .jstree-hovered, #demo4 .jstree-clicked { border:0; }
</style>
<script type="text/javascript">
$(function () {
	$("#demo4")
		.jstree({ "plugins" : ["themes","html_data","ui"] });
});
</script>
</div>

<h2>Using CSS to make the nodes bigger</h2>
<div id="description">
<div id="demo5" class="demo" style="height:120px;">
	<ul>
		<li class="jstree-open">
			<a href="#">Root node 1</a>
			<ul>
				<li>
					<a href="#">Child node 1 with a long text which would normally just cause a scrollbar, but with this line of CSS it will actually wrap, this is not really throughly tested but it works</a>
				</li>
				<li>
					<a href="#">Child node 2</a>
				</li>
			</ul>
		</li>
		<li>
			<a href="#">Root node 2</a>
		</li>
	</ul>
</div>
<style type="text/css" class="source below">
#demo5 li { min-height:22px; line-height:22px; }
#demo5 a { line-height:20px; height:20px; font-size:10px; }
#demo5 a ins { height:20px; width:20px; background-position:-56px -17px; } 
</style>
<script type="text/javascript">
$(function () {
	$("#demo5")
		.jstree({ "plugins" : ["themes","html_data","ui"] });
});
</script>
</div>

<h2>PHP &amp; mySQL demo + event order</h2>
<div id="description">
<p>Here is a PHP &amp; mySQL enabled demo. You can use the classes/DB structure included, but those are not thoroughly tested and not officially a part of jstree. In the log window you can also see all function calls as they happen on the instance.</p>
<div id="mmenu" style="height:30px; overflow:auto;">
<input type="button" id="add_folder" value="add folder" style="display:block; float:left;"/>
<input type="button" id="add_default" value="add file" style="display:block; float:left;"/>
<input type="button" id="rename" value="rename" style="display:block; float:left;"/>
<input type="button" id="remove" value="remove" style="display:block; float:left;"/>
<input type="button" id="cut" value="cut" style="display:block; float:left;"/>
<input type="button" id="copy" value="copy" style="display:block; float:left;"/>
<input type="button" id="paste" value="paste" style="display:block; float:left;"/>
<input type="button" id="clear_search" value="clear" style="display:block; float:right;"/>
<input type="button" id="search" value="search" style="display:block; float:right;"/>
<input type="text" id="text" value="" style="display:block; float:right;" />
</div>

<!-- the tree container (notice NOT an UL node) -->
<div id="demo" class="demo" style="height:200px;"></div>
<div style="height:30px; text-align:center;">
	<input type="button" style='width:170px; height:24px; margin:5px auto;' value="reconstruct" onclick="$.get('./server.php?reconstruct', function () { $('#demo').jstree('refresh',-1); });" />
	<input type="button" style='width:170px; height:24px; margin:5px auto;' id="analyze" value="analyze" onclick="$('#alog').load('./server.php?analyze');" />
	<input type="button" style='width:170px; height:24px; margin:5px auto;' value="refresh" onclick="$('#demo').jstree('refresh',-1);" />
</div>
<div id='alog' style="border:1px solid gray; padding:5px; height:100px; margin-top:15px; overflow:auto; font-family:Monospace;"></div>
<!-- JavaScript neccessary for the tree -->
<script type="text/javascript" class="source below">
$(function () {

$("#demo")
	.bind("before.jstree", function (e, data) {
		$("#alog").append(data.func + "<br />");
	})
	.jstree({ 
		// List of active plugins
		"plugins" : [ 
			"themes","json_data","ui","crrm","cookies","dnd","search","types","hotkeys","contextmenu" 
		],

		// I usually configure the plugin that handles the data first
		// This example uses JSON as it is most common
		"json_data" : { 
			// This tree is ajax enabled - as this is most common, and maybe a bit more complex
			// All the options are almost the same as jQuery's AJAX (read the docs)
			"ajax" : {
				// the URL to fetch the data
				"url" : "./server.php",
				// the `data` function is executed in the instance's scope
				// the parameter is the node being loaded 
				// (may be -1, 0, or undefined when loading the root nodes)
				"data" : function (n) { 
					// the result is fed to the AJAX request `data` option
					return { 
						"operation" : "get_children", 
						"id" : n.attr ? n.attr("id").replace("node_","") : 1 
					}; 
				}
			}
		},
		// Configuring the search plugin
		"search" : {
			// As this has been a common question - async search
			// Same as above - the `ajax` config option is actually jQuery's AJAX object
			"ajax" : {
				"url" : "./server.php",
				// You get the search string as a parameter
				"data" : function (str) {
					return { 
						"operation" : "search", 
						"search_str" : str 
					}; 
				}
			}
		},
		// Using types - most of the time this is an overkill
		// read the docs carefully to decide whether you need types
		"types" : {
			// I set both options to -2, as I do not need depth and children count checking
			// Those two checks may slow jstree a lot, so use only when needed
			"max_depth" : -2,
			"max_children" : -2,
			// I want only `drive` nodes to be root nodes 
			// This will prevent moving or creating any other type as a root node
			"valid_children" : [ "drive" ],
			"types" : {
				// The default type
				"default" : {
					// I want this type to have no children (so only leaf nodes)
					// In my case - those are files
					"valid_children" : "none",
					// If we specify an icon for the default type it WILL OVERRIDE the theme icons
					"icon" : {
						"image" : "./file.png"
					}
				},
				// The `folder` type
				"folder" : {
					// can have files and other folders inside of it, but NOT `drive` nodes
					"valid_children" : [ "default", "folder" ],
					"icon" : {
						"image" : "./folder.png"
					}
				},
				// The `drive` nodes 
				"drive" : {
					// can have files and folders inside, but NOT other `drive` nodes
					"valid_children" : [ "default", "folder" ],
					"icon" : {
						"image" : "./root.png"
					},
					// those prevent the functions with the same name to be used on `drive` nodes
					// internally the `before` event is used
					"start_drag" : false,
					"move_node" : false,
					"delete_node" : false,
					"remove" : false
				}
			}
		},
		// UI & core - the nodes to initially select and open will be overwritten by the cookie plugin

		// the UI plugin - it handles selecting/deselecting/hovering nodes
		"ui" : {
			// this makes the node with ID node_4 selected onload
			"initially_select" : [ "node_4" ]
		},
		// the core plugin - not many options here
		"core" : { 
			// just open those two nodes up
			// as this is an AJAX enabled tree, both will be downloaded from the server
			"initially_open" : [ "node_2" , "node_3" ] 
		}
	})
	.bind("create.jstree", function (e, data) {
		$.post(
			"./server.php", 
			{ 
				"operation" : "create_node", 
				"id" : data.rslt.parent.attr("id").replace("node_",""), 
				"position" : data.rslt.position,
				"title" : data.rslt.name,
				"type" : data.rslt.obj.attr("rel")
			}, 
			function (r) {
				if(r.status) {
					$(data.rslt.obj).attr("id", "node_" + r.id);
				}
				else {
					$.jstree.rollback(data.rlbk);
				}
			}
		);
	})
	.bind("remove.jstree", function (e, data) {
		data.rslt.obj.each(function () {
			$.ajax({
				async : false,
				type: 'POST',
				url: "./server.php",
				data : { 
					"operation" : "remove_node", 
					"id" : this.id.replace("node_","")
				}, 
				success : function (r) {
					if(!r.status) {
						data.inst.refresh();
					}
				}
			});
		});
	})
	.bind("rename.jstree", function (e, data) {
		$.post(
			"./server.php", 
			{ 
				"operation" : "rename_node", 
				"id" : data.rslt.obj.attr("id").replace("node_",""),
				"title" : data.rslt.new_name
			}, 
			function (r) {
				if(!r.status) {
					$.jstree.rollback(data.rlbk);
				}
			}
		);
	})
	.bind("move_node.jstree", function (e, data) {
		data.rslt.o.each(function (i) {
			$.ajax({
				async : false,
				type: 'POST',
				url: "./server.php",
				data : { 
					"operation" : "move_node", 
					"id" : $(this).attr("id").replace("node_",""), 
					"ref" : data.rslt.cr === -1 ? 1 : data.rslt.np.attr("id").replace("node_",""), 
					"position" : data.rslt.cp + i,
					"title" : data.rslt.name,
					"copy" : data.rslt.cy ? 1 : 0
				},
				success : function (r) {
					if(!r.status) {
						$.jstree.rollback(data.rlbk);
					}
					else {
						$(data.rslt.oc).attr("id", "node_" + r.id);
						if(data.rslt.cy && $(data.rslt.oc).children("UL").length) {
							data.inst.refresh(data.inst._get_parent(data.rslt.oc));
						}
					}
					$("#analyze").click();
				}
			});
		});
	});

});
</script>
<script type="text/javascript" class="source below">
// Code for the menu buttons
$(function () { 
	$("#mmenu input").click(function () {
		switch(this.id) {
			case "add_default":
			case "add_folder":
				$("#demo").jstree("create", null, "last", { "attr" : { "rel" : this.id.toString().replace("add_", "") } });
				break;
			case "search":
				$("#demo").jstree("search", document.getElementById("text").value);
				break;
			case "text": break;
			default:
				$("#demo").jstree(this.id);
				break;
		}
	});
});
</script>
</div>

</div>

</body>
</html>