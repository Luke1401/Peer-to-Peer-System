# COMP 3010 Assignment 3 - Hung Lu Dao (7900487)

## Compilation details
Nothing requires compilation

## Running details
You can run the peer by typing: `python3 peer.py <port>` where <port> is the port number you want to set. Or you can try: `python3 peer.py` which will set the port number randomly.

You can run the CLI by typing `python3 node_CLI.py` and enter your command while the program is running, make sure you need to modify the HOST name in program which match to the host_name of peer.

To test the peer, you need to run the `telnet <host> 15000` for CLI to test the status of node by sending command to or run the `node_CLI.py`.

## Features: 
### Gossip Protocol:
  * Periodically sends gossip messages to known peers for discovery and information dissemination.
  * Handles incoming gossip messages to update the peer list and reply with its own details if needed.

### Consensus Mechanism:
  * Implements a Byzantine Fault Tolerance (BFT)-style consensus to agree on database values.
  * Supports recursive consensus with OM (Order of Messages) levels to tolerate malicious or faulty peers.
  * Majority-based decision-making applies the agreed value to the database.

### Peer Management:
  * Discovers and maintains a list of active peers.
  * Removes inactive peers after a timeout period.
  * Replies to gossip requests to assist other peers in the network.

### Database Operations:
  * Maintains a small, shared database among peers.
  * Allows updates (SET command) and queries via the gossip protocol or CLI.

### CLI Commands:
  * Provides local control over the peer node with commands like:
    * `peers`: View all known peers.
    * `current`: Display the database state.
    * `consensus`: Run consensus on a specific database index.
    * `lie/truth`: Toggle dishonest/honest behavior for testing.
    * `set`: Update database values.

### Fault Tolerance:
  * Can simulate "lying" peers to test resilience against malicious nodes.
  * Handles exceptions and errors gracefully to maintain network stability.
