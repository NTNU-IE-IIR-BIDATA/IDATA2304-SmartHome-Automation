
# Work process documentation

## Project plan

We divided the project into 6 distinct milestones, each building upon the previous ones. To simplify the work process,
we divided the project into 6 sprints, one sprint for each milestone. 

- Sprint 1: Project setup, protocol design and basic message handling

- Sprint 2: Server MVP and node registration

- Sprint 3: Simulating sensors sending data to server

- Sprint 4: Control panel with live monitoring of sensor data

- Sprint 5: Send commands from control panel to nodes with sensors and actuators

- Sprint 6: Project finalization, extra add-ons (TLS encryption, UDP discovery)
  
We used separate git branches for developing new features, merging them into main upon completion. 

## Task distribution

All group members have worked on the programming and core parts of the system:

- Sondre Namløs Lassen: Wrote the communication protocol, message formatting, core server connections, control panel UI with anomaly detection, auto-reconnect, UDP server discovery, CLI options for server and control panel, and documentation updates
- Håkon Lunde Risa: Setup of the repository, message validation, development of sensor-actuator-nodes, sensor simulation, actuator command execution, control panel client, support for multiple nodes, improving error handling and TLS encryption
- Elias Farstad Vartdal: Implemented message framing tests, state updates on the server, sensor reporting loop, control panel registration and live server broadcasting,live UI integration, server command routing, user roles and wildcard (ALL) support

## Breaking down work into issues

Before each sprint, we broke the milestone down into smaller tasks, delegating responsibility and a definition of done (DoD)
so everyone knew when it was finished. We mostly worked on the project while sitting together, so we defined and delegated the issues
verbally rather than using a tool like GitHub Isses.

---

## Sprint reports and retrospectives

### Sprint 1: Setup and basic messaging

Goal: Setting up the project, agree on how everything communicates and building the basic message handling.

Planned Issues:

- Setting up project roadmap (Sondre, Håkon).
  - Description: Creating the repo with folder structure and formulating a milestone plan
  - DoD: Everyone clones the project and setup to their local machine and agrees on the plan
  
- Writing communication protocol (Sondre)
  - Description: Define what messages, fields, roles and errors used in the system
  - DoD: Protocol covers all core communications and satisfies all project requirements
  
- Implement message formatting and error helpers (Sondre)
  - Description: Encoding and decoding of text sent over the network, and creating standard error messages
  - DoD: Messages encode and decode as expected, error messages can be created

- Add message validation and tests (Håkon)
  - Description: Check that ingoing and outgoing messages have the correct fields
  - DoD: Invalid messages are rejected, unit tests pass

- Add tests for message formatting (Elias)
  - Description: Test encoding and decoding and broken/invalid inputs
  - DoD: All unit tests pass

All planned issues were completed in this sprint

Retrospective:

- What went well: Completing the protocol early made it easy to work in parallell throughout the project
- What to improve: We re-organized the folder structure halfway through, so planning the layout better from the start would have saved some time

---

### Sprint 2: Core server and node registration

Goal: Get the server running, letting a node connect and register

Planned Issues:

- Basic server connection handling (Sondre)
  - Description: Make the server listen for connections and routing of incoming messages
  - DoD: Server accepts connections, unit tests passing

- Creating initial Sensor-Actuator nodes (Håkon)
  - Description: Make a node and connect it to the server, sending it a list of connected sensors and actuators
  - DoD: Node connects and registers on the server

- Track registered nodes on the server (Elias)
  - Description: Store connected nodes and their sensors and actuators in the server state
  - DoD: Server keeps track of registered nodes, unit tests pass

All planned issues were completed in this sprint

Retrospective:

- What went well: Splitting the server, node and state let us code together at the same time
- What to improve: There were some issues with merging the branches at the end. Merging into main more often would have made it easier

---

### Sprint 3: Simulating sensors and live data

Goal: Make nodes generate sensor data and send them to the server automatically

Planned Issues:

- Add simulated sensors (Håkon)
  - Description: Create simulated sensors that give realistic values
  - DoD: Different sensor types generate data

- Send sensor data automatically (Elias)
  - Description: Make nodes read their sensor data every few seconds and sent it to the server
  - DoD: Connected nodes send sensor data at the specified interval
  
- Update server state with new data (Sondre)
  - Description: Save the incoming sensor data to the server state
  - DoD: Server state updates with the incoming data

All planned issues were completed in this sprint

Retrospective:

- What went well: This sprint went quite smooth, since the basic connections from the previous sprint worked
- What to improve: We had miscommunicated the data types which were to be sent, so we had to do some refactoring to make the system support different data types. Clearer communication could have saved some refactoring.

---

### Sprint 4: Control panel and live monitoring

Goal: Create a control panel and UI so users can see live data, status updates and warnings

Planned Issues:

- Support control panels on the server (Elias)
  - Description: Let control panels register, receive the current system state and get live sensor updates
  - DoD: Control panels get the current state and live updates

- Create the control panel client (Håkon)
  - Description: Connect the control panel to the server and handle the incoming updates
  - DoD: Client connects, registers and updates its state

- Create the terminal UI and anomaly detection (Sondre)
  - Description: Show connected devices in the terminal and display warnings when sensor data is not in a specified normal state
  - DoD: UI shows live data and flags not normal sensor data

- Connect UI to the live server data (Elias)
  - Description: Hook the UI up to the control panel client so that it displays real data
  - DoD: Running the server, node and panel toghether shows live data updates, passes integration tests

All planned issues were completed in this sprint

Retrospective:

- What went well: Integration tests helped us verify everything was working correctly. More or less no friction when merging the different branches into main
- What to improve: The sprint took a while to complete because all parts had to line up. Cheching in more in the middle could have helped keep things moving

---

### Sprint 5: Controlling actuators

Goal: Let users write commands in the control panel UI and see the updated state

Planned Issues:

- Handle actuator commands on nodes (Håkon)
  - Description: Run the incoming commands on the nodes actuators, confirm the new state and return errors for invalid commands
  - DoD: Actuators change on correct commands, errors returns if not

- Route actuator commands on the server (Elias)
  - Descripton: Forwarding of commands from the control panel to the right nodes and send the updated state to the control panel
  - DoD: Commands reach target node, state update shows up on all panels

- Add command input and state updates in the control panel (Sondre)
  - Description: Let users input actuator commands in the UI and show the updated actuator states
  - DoD: Commands can be sent from the UI, state updates show

All planned issues were completed in this sprint

Retrospective:

- What went well: Splitting the work cleanly allowed us to complete the sprint quickly
- What to improve: We started implementing some sprint 6 branches before sprint 5 was fully completed, which made the merging a total mess

---

### Sprint 6: Project finalization and extra features

Goal: Finalize the project and add extra features such as ALL wildcard identifier, TLS encryption and automatic server discovery

Planned Issues:

- Support running multiple customizable nodes (Håkon)
  - Description: Adding CLI arguments to allow running nodes with different id's, sensors, actuators etc.
  - DoD: Multiple different nodes can run at the same time

- Add user roles and ALL wildcard (Elias)
  - Description: Restrict what commands different users are allowed to execute. Allow targeting all actuators and/or nodes using the 'ALL' keyword
  - DoD: Unauthorized commands are blocked and wildcard commands work

- Improve server error handling and validation (Håkon)
  - Description: Make sure bad messages are handles without crashing the server
  - DoD: Invalid messages get clear error responses, repeated errors cause the connection to close

- Add CLI args, node status display and auto reconnect (Sondre)
  - Description: Add support for CLI arguments for the server and control panel. Show online/offline node status, and reconnect automatically if connections close
  - DoD: Components accept CLI arguments, node status showing in UI, panels and nodes reconecct automatically

- Add support for TLS encryption (Håkon)
    - Description: Add option to use TLS encryption for messages between control panels, server and nodes
    - DoD: All components can communicate using TLS
  
- Add automatic UDP server discovery (Sondre)
  - Description: Let nodes and control panels automatically discover the server on local networks
  - DoD: Clients started with the discovery option finds and connects to the server

- Update documentation and final cleanups (Sondre, Håkon)
  - Description: Update the README and protocol, fix code formatting and linting, add AI declaration
  - DoD: Docs match the finished app, all tests and linters pass

All planned issues were completed in this sprint

Retrospective:

- What went well: Finished implementing all features, including some extra ones well ahead of final delivery date
- What to improve: Implementing a lot of features over two days led to several merge conflicts. Taking better time could have prevented this.