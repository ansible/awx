<?php
require_once("config.php");
$jstree = new json_tree();

//$jstree->_create_default();
//die();

if(isset($_GET["reconstruct"])) {
	$jstree->_reconstruct();
	die();
}
if(isset($_GET["analyze"])) {
	echo $jstree->_analyze();
	die();
}

if($_REQUEST["operation"] && strpos($_REQUEST["operation"], "_") !== 0 && method_exists($jstree, $_REQUEST["operation"])) {
	header("HTTP/1.0 200 OK");
	header('Content-type: application/json; charset=utf-8');
	header("Cache-Control: no-cache, must-revalidate");
	header("Expires: Mon, 26 Jul 1997 05:00:00 GMT");
	header("Pragma: no-cache");
	echo $jstree->{$_REQUEST["operation"]}($_REQUEST);
	die();
}
header("HTTP/1.0 404 Not Found"); 
?>

<?php
/*
$jstree->_drop();
$jstree->create_node(array("id"=>0,"position"=>0));
$jstree->create_node(array("id"=>1,"position"=>0));
$jstree->create_node(array("id"=>1,"position"=>0));
$jstree->create_node(array("id"=>3,"position"=>0,"name"=>"Pesho"));
$jstree->move(3,2,0,true);
$jstree->_dump(true);
$jstree->_reconstruct();
echo $jstree->_analyze();
die();

$tree = new _tree_struct;
$tree->drop();
$tree->create(0, 0);
$tree->create(0, 0);
$tree->create(1, 0);
$tree->create(0, 3);
$tree->create(2, 3);
$tree->create(2, 0);
$tree->dump(true);
$tree->move(6,4,0);
$tree->move(1,0,0);
$tree->move(3,2,99,true);
$tree->move(7,1,0,true);
$tree->move(1,7,0);
$tree->move(1,0,1,true);
$tree->move(2, 0, 0, true);
$tree->move(13, 12, 2, true);
$tree->dump(true);
$tree->move(15, 16, 2, true);
$tree->dump(true);
$tree->move(4, 0, 0);
$tree->dump(true);
$tree->move(4, 0, 2);
$tree->dump(true);
echo $tree->analyze();
$tree->drop();
*/
?>