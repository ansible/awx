<?php
class _database {
	private $data		= false;
	private $result		= false;
	private $row		= false;

	public $settings	= array(
			"servername"=> "localhost",
			"serverport"=> "3306",
			"username"	=> false,
			"password"	=> false,
			"database"	=> false,
			"persist"	=> false,
			"dieonerror"=> false,
			"showerror"	=> false,
			"error_file"=> true
		);

	function __construct() {
		global $db_config;
		$this->settings = array_merge($this->settings, $db_config);
		if($this->settings["error_file"] === true) $this->settings["error_file"] = dirname(__FILE__)."/__mysql_errors.log";
	}

	function connect() {
		$this->data = new mysqli(
			$this->settings["servername"], 
			$this->settings["username"], 
			$this->settings["password"], 
			$this->settings["database"],
			$this->settings["serverport"]
		);

		if(mysqli_connect_errno()) { 
			$this->error("Connection error: ".mysqli_connect_error() ); 
			return false; 
		}
		if(!$this->data->set_charset("utf8")) {
			$this->error("Error loading character set utf8");
			return false;
		}
		return true;
	}

	function query($sql) {
		if(!$this->data && !$this->connect()) {
			$this->error("Could node connect for query: ".$sql);
			return false;
		}
		//echo $sql."<br />:";
		if(!($this->result = $this->data->query($sql))) $this->error($sql);
		return ($this->result) ? true : false;
	}
	
	function nextr(){
		if(!$this->result) {
			$this->error("No query pending");
			return false;
		}
		unset($this->row);
		$this->row = $this->result->fetch_array(MYSQL_BOTH);
		return ($this->row) ? true : false ;
	}

	function get_row($mode = "both") {
		if(!$this->row) return false;

		$return = array();
		switch($mode) {
			case "assoc":
				foreach($this->row as $k => $v) {
					if(!is_int($k)) $return[$k] = $v;
				}
				break;
			case "num":
				foreach($this->row as $k => $v) {
					if(is_int($k)) $return[$k] = $v;
				}
				break;
			default:
				$return = $this->row;
				break;
		}
		return array_map("stripslashes",$return);
	}

	function get_all($mode = "both", $key = false) {
		if(!$this->result) {
			$this->error("No query pending");
			return false;
		}
		$return = array();
		while($this->nextr()) {
			if($key !== false) $return[$this->f($key)] = $this->get_row($mode);
			else $return[] = $this->get_row($mode);
		}
		return $return;
	}

	function f($index) {
		return stripslashes($this->row[$index]);
	}

	function go_to($row) {
		if(!$this->result) {
			$this->error("No query pending");
			return false;
		}
		if(!$this->data->data_seek($row)) $this->error();
	}

	function nf() {
		if (!$this->result) {
			$this->error("nf: no result set");
			return false;
		}
		return $this->result->num_rows;
	}
	function af() {
		return $this->data->affected_rows;
	}
	function error($string = "") {
		$error = $this->data->error;
		if($this->settings["show_error"]) echo $error;
		if($this->settings["error_file"] !== false) {
			$handle = @fopen($this->settings["error_file"], "a+");
			if($handle) {
				@fwrite($handle, "[".date("Y-m-d H:i:s")."] ".$string." <".$error.">\n");
				@fclose($handle);
			}
		}
		if($this->settings["dieonerror"]) {
			if(isset($this->result)) $this->result->free();
			@$this->data->close();
			die();
		}
	}
	function insert_id() {
		return $this->data->insert_id;
	}
	function escape($string) {
		if(!$this->data) return addslashes($string);
		return $this->data->escape_string($string);
	}

	function destroy() {
		if(isset($this->result)) $this->result->free();
		if($this->data) $this->data->close();
	}


}