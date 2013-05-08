<?php
class _database {
	private $link		= false;
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
		if (!$this->link) {
			$this->link = ($this->settings["persist"]) ? 
				mysql_pconnect(
					$this->settings["servername"].":".$this->settings["serverport"], 
					$this->settings["username"], 
					$this->settings["password"]
				) : 
				mysql_connect(
					$this->settings["servername"].":".$this->settings["serverport"], 
					$this->settings["username"], 
					$this->settings["password"]
				) or $this->error();
		}
		if (!mysql_select_db($this->settings["database"], $this->link)) $this->error();
		if($this->link) mysql_query("SET NAMES 'utf8'");
		return ($this->link) ? true : false;
	}

	function query($sql) {
		if (!$this->link && !$this->connect()) $this->error();
		if (!($this->result = mysql_query($sql, $this->link))) $this->error($sql);
		return ($this->result) ? true : false;
	}
	
	function nextr() {
		if(!$this->result) {
			$this->error("No query pending");
			return false;
		}
		unset($this->row);
		$this->row = mysql_fetch_array($this->result, MYSQL_BOTH);
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
		if(!mysql_data_seek($this->result, $row)) $this->error();
	}

	function nf() {
		if ($numb = mysql_num_rows($this->result) === false) $this->error();
		return mysql_num_rows($this->result);
	}
	function af() {
		return mysql_affected_rows();
	}
	function error($string="") {
		$error = mysql_error();
		if($this->settings["show_error"]) echo $error;
		if($this->settings["error_file"] !== false) {
			$handle = @fopen($this->settings["error_file"], "a+");
			if($handle) {
				@fwrite($handle, "[".date("Y-m-d H:i:s")."] ".$string." <".$error.">\n");
				@fclose($handle);
			}
		}
		if($this->settings["dieonerror"]) {
			if(isset($this->result)) mysql_free_result($this->result);
			mysql_close($this->link);
			die();
		}
	}
	function insert_id() {
		if(!$this->link) return false;
		return mysql_insert_id();
	}
	function escape($string){
		if(!$this->link) return addslashes($string);
		return mysql_real_escape_string($string);
	}

	function destroy(){
		if (isset($this->result)) mysql_free_result($this->result);
		if (isset($this->link)) mysql_close($this->link);
	}


}
?>