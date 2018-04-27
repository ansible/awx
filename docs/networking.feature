Feature: Networking Topology Visualization
    In order to increase the ease and understanding of network automation
    As as network engineer
    I want a visualization of the network topology so that I can
    easily understand how the network topology is connected

    Scenario: Blank canvas
        Given an ansible inventory
        When the user clicks on the network topology icon for that inventory
        Then populate the toolbox with the data loaded from inventory

    Scenario: Device Organization
        Given an ansible inventory loaded into the canvas toolbox
        When the user clicks and drags on a device in the inventory toolbox
        Then place the device onto the topology canvas at the location of the user's mouse pointer

    Scenario: Link Connection
        Given an ansible inventory loaded into the canvas toolbox
        When the user clicks and drags on a device in the inventory toolbox
        Then automatically draw lines and circles that represent the links
        And interfaces of the connected devices.

    Scenario: Customize Layout
        Given a canvas populated with a network topology
        When the user clicks and drags on a device on the topology canvas
        Then move the device to the location of the user's mouse pointer
        And update the links and interfaces representations

    Scenario: Export SVG
        Given a canvas populated with a network topology
        When the user clicks on the Export SVG button
        Then capture the current view of the canvas
        And download an SVG file of the canvas to the users computer

    Scenario: Export YAML
        Given a canvas populated with a network topology
        When the user clicks on the Export YAML button
        Then capture the state of the current view of the canvas
        And download a YAML file that represents the data to the user's computer

    Scenario: Pan
        Given a canvas populated with a network topology
        When the user clicks and drags on the background
        Then move the viewport of the virtual canvas to match the user's mouse movement

    Scenario: Zoom
        Given a canvas populated with a network topology
        When the user scrolls their mousewheel or clicks and drags on the zoom widget
        Then scale the viewport of the virtual canvas to the zoom level reflected on the zoom widget

    Scenario: Hide information when zooming out
        Given a canvas populated with a network topology
        When the user zooms out via mouse wheel or zoom widget
        Then hide low-level information to provide a high-level overview as the zoom level changes

    Scenario: Show more information when zooming in
        Given a canvas populated with a network topology
        When the user zooms in via mouse wheel or zoom widget
        Then show more low-level information to provide more detail for the devices that are in view on the virtual canvas

    Scenario: Device Detail
        Given a canvas populated with a network topology
        When the user clicks on show details device context menu button
        Then show the device details including name, description, and host vars

    Scenario: Remove Device
        Given a canvas populated with a network topology
        When the user clicks on remove device context menu button
        Then remove the device and connected links from the canvas
        And return the device to the inventory toolbox

    Scenario: Search by Device Name
        Given a canvas populated with a network topology
        When the user types the device name or selects it from a device drop down list
        Then position the viewport on the virtual canvas over the device with that name

