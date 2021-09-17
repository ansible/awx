# Automation Platform Mesh Inventory Examples
<b><i>Note</b> - we use the term `mesh` in this document to describe a network comprising of vertices or `nodes`. Communication between nodes is defined by the term `edges`, or in computer terms, a connection on the transport layer such as `TCP`, `UDP` or `unix sockets`.</i>

Please refer to [this](./receptor_mesh.md) document for a more in-depth explanation of the objects in the `mesh` network. 

The examples below are an attempt to deliver `ansible` inventory files that reflect typical user environments. While we cannot encapsulate every single customer scenario, if you need a starting point to start building out your inventory file, please refer to the examples [below](##Example-Inventory-Files).

| Node Type | Description |
| --------- | ----------- |
| Control | Nodes that run persistent AWX services, and delegate jobs to hybrid and execution nodes|
| Hybrid | Nodes that run persistent AWX services and execute jobs from user-space|
| Hop | Actionless nodes in a given network. They will have [receptor](./receptor_mesh.md) but remain actionless |
| Execution | Nodes that run jobs delivered from Control-Nodes (jobs submitted from the user-space) |

## Example Inventory Files
--------------------------

### Standard Control Plane (3 Node) and (n)-Execution Nodes
![](./img/three_node_control_plane_n_execution_nodes.png)
<details>
    <summary>Code for Inventory File</summary>
</details>

### Standard Control plane and Execution Topology with Hop Nodes

![](./img/three_node_control_plane_n_execution_nodes_with_hops.png)
<details>
    <summary>Code for Inventory File</summary>
</details>

### Single Control-Node only Deployment (Non-Hybrid)
![](./img/single_control_node_only.png)
<details>
    <summary>Code for Inventory File</summary>
</details>

### (n)-Node Control-Only Deployment (Non-Hybrid)
![](./img/n_control_nodes_only.png)
<details>
    <summary>Code for Inventory File</summary>
</details>

### Single Hybrid-Node-Only Deployment
![](./img/single_hybrid_node_only.png)
<details>
    <summary>Code for Inventory File</summary>
</details>

### (n)-Node Hybrid-Node Deployment
#### <i>Similar to (n)-Node Control-Only Deployment (Non-Hybrid)</i>
![](./img/n_hybrid_nodes.png)
<details>
    <summary>Code for Inventory File</summary>
</details>

### Single Control Plane and Single Execution Node
![](./img/)
<details>
    <summary>Code for Inventory File</summary>
</details>