import sys
import select
import json
import socket
import time
import random
import uuid
import string
import re
import traceback

from collections import Counter


# Constants
host_name = socket.gethostname()
HOST = socket.gethostbyname(host_name)
PORT = 8999
CLI_PORT = 8888
NAME = "Luke's peer on " + host_name
ID = str(uuid.uuid4())

PORT_MIN = 1024
PORT_MAX = 65535
GOSSIP_REPEAT_DURATION = 60 # GOSSIP every minute
TIMEOUT = 120 # drop node after 2 minutes if not send a GOSSIP
KNOWN_PEERS = [
    ("owl.cs.umanitoba.ca", 16000),
    ("eagle.cs.umanitoba.ca", 16000),
    ("hawk.cs.umanitoba.ca", 16000),
    ("osprey.cs.umanitoba.ca", 16000)
]

KNOWN_HOST = "130.179.28.51"
KNOWN_PORT = 16000
DATABASE_SIZE = 5

database = ["Lucifer", "Hung Lu Dao", "Luke", "Minato", "Itachi"]

last_gossip_times = {}
last_gossip_sent_time = time.time()


def get_random_port():
    return random.randint(PORT_MIN, PORT_MAX)

def generate_random_word(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def generate_lie_percentage():
    return random.randint(1,100) / 100


class HandleInput:
    def __init__(self, host, port):
        self.HOST = host
        self.PORT = port

    def handle_input(self):
        if len(sys.argv) == 1:
            self.PORT = get_random_port()
        elif len(sys.argv) == 2:
            try:
                self.PORT =  int(sys.argv[1])
            except ValueError:
                print("Bad port number")
                sys.exit(1)
        else:
            print("Usage: python3 peer.py [port]")
            sys.exit(1)

    def get_host(self):
        return self.HOST

    def get_port(self):
        return self.PORT



class Peer:
    peer_list = []
    def __init__(self, peer_host = None, peer_port = None):
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.timeout = time.time() + TIMEOUT
        self.last_word = ""
    
    def get_host(self):
        return self.peer_host
    
    def get_port(self):
        return self.peer_port

    def add_peer(self, peer):
        if peer not in self.peer_list:
            self.peer_list.append(peer)

    def drop_peer(self, peer):
        self.peer_list.remove(peer)

    def get_peers(self):
        return self.peer_list
    
    def get_last_word(self):
        return self.last_word
    
    def set_last_word(self, word):
        self.last_word = word

# keep track of current words that other peers send to
word_list = []
class Protocols:
    def __init__(self, peer:Peer):
        peer.add_peer(peer)
        self.peers = peer.get_peers()
        self.gossips = [] # keep track of message ID of gossip that we known
        self.consensus = [] # keep track of message ID of consensus that we known 
        self.incorrect_word = None
        self.lie_mode = False
        self.counter = 0
    def get_peers(self): 
        return self.peers
    
    def remove_peer(self, peer:Peer):
        if peer in self.peers:
            print(f"Time out, remove the unactive peer: {peer.peer_host}:{peer.peer_port}")
            self.peers.remove(peer)
        else:
            print(f"We already remove this peer: {peer.peer_host}:{peer.peer_port}. PASS")
    
    def start_lying(self, lie_percent):
        self.lie_mode = True
        self.incorrect_word = generate_random_word(10)
        print(f"Start lying, my word is {self.incorrect_word} and the lie percentage is {lie_percent}%")

    def stop_lying(self):
        self.lie_mode = False


    # send announce a GOSSIP to enter
    def send_announce(self):
        response = {
            "command": "GOSSIP",
            "host": HOST,
            "port": PORT,
            "name": NAME,
            "messageID": ID
        }
        print(f"Sending announce to join the network: {str(response)}")
        # join the netowrk by send GOSSIP to two of well-known peers
        selected_peers = random.sample(KNOWN_PEERS, 2)
        try:
            for peer in selected_peers:
                SOCKET.sendto(json.dumps(response).encode(), peer)
        except Exception as e:
            print(f"Error in send announce to well known peers to join the network: {e}")
            traceback.print_exc()

    # send GOSSIP to up to 5 randomly chosen known peers
    def send_gossip(self):
        message = {
            "command": "GOSSIP",
            "host": HOST,
            "port": PORT,
            "name": NAME,
            "messageID": ID
        }
        print(f"Sending gossip: {str(message)}")
        # send it to up to 5 randomly chosen known peers
        if len(self.peers) < 5:
            chosen_peers = self.peers
        else:
            chosen_peers = random.sample(self.peers, 5)
        try:
            for peer in chosen_peers:
                SOCKET.sendto(json.dumps(message).encode(),(peer.peer_host, peer.peer_port))
        except Exception as e:
            print(f"Error in sending gossip to general:{e}")
            traceback.print_exc()

    # receive a GOSSIP message, reply to the peer listed with my information if this node was previously unknown to me
    def send_receive_gossip(self, message):
        print(f"Receive gossip is: {str(message)}")
        peer_host = message["host"]
        peer_port = message["port"]
        new_peer = Peer(peer_host, peer_port)
        response = {
            "command": "GOSSIP_REPLY",
            "host": HOST,
            "port": PORT,
            "name": NAME
        }
        # check if this peer is unknown to me
        try:
            if new_peer not in self.peers:
                peer_name = message["name"]
                print(f"Reply to the peer: {peer_name} with my response is: {response}")
                SOCKET.sendto(json.dumps(response).encode(), (message["host"], message["port"]))
        except Exception as e:
            print(f"Error in replying GOSSIP to the peer: {e}")
            traceback.print_exc()
        

    # Reply to the original sender
    def send_gossip_reply(self, host, port):
        response = {
            "command": "GOSSIP_REPLY",
            "host": HOST,
            "port": PORT,
            "name": NAME
        }
        print(f"Sending gossip reply to original sender: {str(response)}")
        # send GOSSIP_REPLY back to the one who sent the original gossip message
        try:
            SOCKET.sendto(json.dumps(response).encode(), (host, port))
        except Exception as e:
            print(f"Error in sending back the gossip reply to original sender")
            traceback.print_exc()

    def reset_gossip(self):
        print("Reset gossip, send GOSSIP every minute.")
        self.gossips = []

    def handle_gossip_reply(self, message):
        try:
            peer = Peer(message["host"], message["port"])

            # check not getting duplicate peer in my peer list
            if peer not in self.peers and message["name"] != NAME:
                last_gossip_times[peer] = time.time()
                self.peers.append(peer)

        except Exception as e:
            print(f"The given gossip reply had an error {e}.")
            traceback.print_exc()


    # when we get a gossip message, we know that we successfully joined the network
    def handle_gossip(self, message):
        self.counter += 1
        try:
            my_host = message["host"]
            my_port = message["port"]
            
            if self.counter == 1: # first time i heard it
                # forward the message verbatim to up to 5 peers
                self.send_gossip()
                # reply to the original sender
                self.send_gossip_reply(my_host, my_port)
            else:
                # reply to the peer listed with my information 
                self.send_receive_gossip(message)

        except Exception as e:
            print(f"Error in handling gossip: {e}")
            traceback.print_exc()
    
    def send_message_to_all_peers(self, message):
        for peer in self.peers:
            try:
                SOCKET.sendto(json.dumps(message).encode(), (peer.peer_host, peer.peer_port))
            except Exception as e:
                print(f"Error in sending message: {e}")
                traceback.print_exc()

    def get_max_OM_level(self):
        if len(self.peers) <= 0:
            raise ValueError("Number of peers must be greater than 0")

        return (len(self.peers) - 1) // 3

    def send_consensus(self, index):
        om_level = self.get_max_OM_level()
        message = {
            "command": "CONSENSUS",
            "OM": om_level,
            "index": index,
            "value": database[index],
            "peers": [(peer.peer_host, peer.peer_port) for peer in self.peers],
            "messageID": ID,
            "due": time.time() + GOSSIP_REPEAT_DURATION
        }
        print(f"Sending consensus: {str(message)}")
        self.send_message_to_all_peers(message)
    
    def send_sub_consensus(self, message, om_level):
        message = {
            "command": "CONSENSUS",
            "OM": om_level,
            "index": message["index"],
            "value": message["value"],
            "peers": [(peer.peer_host, peer.peer_port) for peer in self.peers],
            "messageID": str(uuid.uuid4()),
            "due": time.time() + GOSSIP_REPEAT_DURATION/2
        }
        print(f"Sending sub consensus: {str(message)}")
        self.send_message_to_all_peers(message)
        
    def send_consensus_reply(self, message, address):
        lie_percent = generate_lie_percentage()
        if lie_percent > 0.8: # being a traitor :))
            self.start_lying(lie_percent)
            consensus_value = self.incorrect_word
        else: 
            self.stop_lying()
            consensus_value = message["value"]
        message_id = message["messageID"]
        
        word_list.append(consensus_value)
        
        om_level = message["OM"]
        while om_level > 0: # doing recursive OM(m-1)
            # perform an OM(m-1) consensus
            om_level -= 1
            self.send_sub_consensus(message, om_level)
        
        if om_level == 0: # OM(0): send current value back to the commander
            response = { 
                "command": "CONSENSUS_REPLY",
                "value": consensus_value,
                "reply-to": message_id
            }
            print(f"Sending consensus reply to commander: {str(response)}")
            try:
                SOCKET.sendto(json.dumps(response).encode(), address)
            except Exception as e:
                print(f"Error in sending consensus reply: {e}")
                traceback.print_exc()


    def handle_consensus(self, message, address):
        index = int(message["index"])

        # as a commander, send consensus to other peers in network
        self.send_consensus(index)

        # as a lieutenant, perform recursive to send consensus value to peers if OM level > 0 or send current value back to commander
        self.send_consensus_reply(message, address)

        # as a commander, send back the value that appears most often
        self.send_back_result_to_commander(message, address)

    
    def handle_consensus_reply(self, message, address):
        message_id = message["reply-to"]
        value = message["value"]
        word_list.append(value)
        peer = Peer(address)
        if message_id not in self.consensus:
            self.consensus.append(message_id)
            peer.set_last_word(value)
            print(f"The peer {peer.peer_host}:{peer.peer_port} has the last word is {value}")

    
    def find_majority(self, word_list):

        # Create a Counter object to count the frequency of each word
        word_counts = Counter(word_list)
        # Find the word with the highest frequency
        result, count = word_counts.most_common(1)[0]

        return result

    def send_back_result_to_commander(self, message, address):
        word = self.find_majority(word_list)
        # apply the value to my database
        index = message["index"]
        database[index] = word
        response = {
            "command": "CONSENSUS_REPLY",
            "value": word,
            "reply-to": message["messageID"]
        }
        print(f"Sending final value to commander: {str(response)}")
        try:
            SOCKET.sendto(json.dumps(response).encode(), address)
        except Exception as e:
            print(f"Error in sending final value: {e}")
            traceback.print_exc()


    def send_query(self):
        query_message = {
            "command": "QUERY"
        }
        print(f"Sending query: {str(query_message)}")
        for peer in self.peers:
            try:
                SOCKET.sendto(json.dumps(query_message).encode(), (peer.peer_host, peer.peer_port))
            except Exception as e:
                print(f"Error ins sending query: {e}")
                traceback.print_exc()

    def send_query_reply(self, address):

        query_reply = {
            "command": "QUERY_REPLY",
            "database": database
        }
        print(f"Sending query reply: {str(query_reply)}")
        try:
            SOCKET.sendto(json.dumps(query_reply).encode(), address)
        except Exception as e:
            print(f"Error in sending query reply: {e}")
            traceback.print_exc()


    def handle_query(self, address):

        # send query to the given address
        self.send_query()

        # send query reply to the given address
        self.send_query_reply(address)



    def handle_query_reply(self, message):
        database = message["database"]
        print(f"Handle the QUERY-REPLY, the database is: {database}")

    def set_word(self, index, word):
        if 0 <= index < DATABASE_SIZE:
            database[index] = word
            print(f"SET command: set the value: {word} at index: {index}")
        else:
            print(f"Invalid index {index} for SET command.")
    
    def send_set(self, index, value):
        response = {
            "command": "SET",
            "index": index,
            "value": value
        }
        print(f"Sending set: {str(response)}")
        self.send_message_to_all_peers(response)



    def handle_set(self, message, address):
        index = message["index"]
        value = message["value"]
        print(f"SET command: set the value: {value} at index: {index} from {address}")
        self.set_word(index, value)

        # send set to other peers in the network
        #self.send_set(index, value)


class ProcessCommand:
    def __init__(self):
        self.protocols = Protocols(Peer(KNOWN_HOST, KNOWN_PORT))

    def join_network(self):
        self.protocols.send_announce()

    def send_gossip(self):
        self.protocols.send_gossip()
    
    def reset_gossip(self):
        self.protocols.reset_gossip()

    def remove_peer(self, peer:Peer):
        self.protocols.remove_peer(peer)

    def process_command(self, message, address):
        try:
            json_message = json.loads(message)
            if json_message["command"] == "GOSSIP":
                self.protocols.handle_gossip(json_message)

            elif json_message["command"] == "GOSSIP-REPLY" or json_message["command"] == "GOSSIP_REPLY":
                self.protocols.handle_gossip_reply(json_message)

            elif json_message["command"] == "CONSENSUS":
                self.protocols.handle_consensus(json_message, address)

            elif json_message["command"] == "CONSENSUS-REPLY" or json_message["command"] == "CONSENSUS_REPLY":
                self.protocols.handle_consensus_reply(json_message, address)

            elif json_message["command"] == "QUERY":
                self.protocols.handle_query(address)

            elif json_message["command"] == "QUERY-REPLY" or json_message["command"] == "QUERY_REPLY":
                self.protocols.handle_query_reply(json_message)

            elif json_message["command"] == "SET":
                self.protocols.handle_set(json_message, address)
            
            else:
                print("Invalid command request!")
        except Exception as e:
            print(f"Bad JSON format {e}")
        
        
class Node_CLI:
    def __init__(self):
        self.protocols = Protocols(Peer(HOST, CLI_PORT))

    def do_peers(self, cli_socket):
        peers = self.protocols.get_peers()
        result = ""
        for peer in peers:
            result += f"Peer: {(peer.get_host(), peer.get_port())}, Last word: {peer.get_last_word()}\r\n"
        cli_socket.sendall(f"Handle peers command: List all known peers, with last words received from each.\r\n {result}".encode())

    def do_current(self, cli_socket):
        cli_socket.sendall(f"Handle current command: Show the current word list\r\nThe word list is: {word_list}".encode())
    
    def do_consensus(self, index, cli_socket):
        try:
            index = int(index)
            self.protocols.send_consensus(index)
            cli_socket.sendall(f"Handle consensus command: Run consensus for a given index\r\nConsensus run for index {index}.".encode())
        except ValueError:
            cli_socket.sendall(b"Invalid index. Please provide a numeric index")
    
    def do_lie(self, cli_socket):
        cli_socket.sendall(b"Handle lie command: Lie all the time")
        lie_percent = generate_lie_percentage()
        self.protocols.start_lying(lie_percent)
    
    def do_truth(self, cli_socket):
        cli_socket.sendall(b"Handle truth command: always return 'honest' answers.")
        self.protocols.stop_lying()

    def do_set(self, index, word, cli_socket):
        try:
            index = int(index)
            self.protocols.set_word(index, word)
            cli_socket.sendall(f"Set word: {word} at index {index} into the database".encode())
        except ValueError:
            cli_socket(b"Invalid index, Please provide a numeric index.")
    
    def do_exit(self, cli_socket):
        cli_socket.sendall(b"Exit the command-line interface.")
        sys.exit(0)
        return True
    
    def handle_command(self, command, x, y, cli_socket):
        if command == "peers":
            self.do_peers(cli_socket)
        elif command == "current":
            self.do_current(cli_socket)
        elif command == "consensus":
            self.do_consensus(x, cli_socket)
        elif command == "lie":
            self.do_lie(cli_socket)
        elif command == "truth":
            self.do_truth(cli_socket)
        elif command == "set":
            self.do_set(x, y, cli_socket)
        elif command == "exit":
            self.do_exit(cli_socket)
        else:
            print("Invalid command!")
        


handle_input = HandleInput(HOST, PORT)
handle_input.handle_input()

HOST = handle_input.get_host()
PORT = handle_input.get_port()


SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SOCKET.bind((HOST, PORT))

CLI_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
CLI_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
CLI_SOCKET.bind((HOST, CLI_PORT))
CLI_SOCKET.listen(5)


print(f"listening on interface: {HOST}")
print(f"listening on port: {PORT} and CLI port: {CLI_PORT}")


process_command = ProcessCommand()
process_command.join_network()
process_command.send_gossip()

cli_command = Node_CLI()

inputs = [SOCKET, CLI_SOCKET]
outputs = []
cli_connections = []
while True:
    try:

        next_gossip_time = last_gossip_sent_time + GOSSIP_REPEAT_DURATION
        readable, writable, exceptional = select.select(inputs, outputs, inputs, TIMEOUT)

        for source in readable:
            if source is SOCKET:
                data, addr = source.recvfrom(4096)
                process_command.process_command(data, addr)
            elif source is CLI_SOCKET:
                conn, addr = CLI_SOCKET.accept()
                inputs.append(conn)
                cli_connections.append(conn)
            elif source in cli_connections:
                data = source.recv(4096).decode("utf-8")  # Ensure data is decoded properly
                if data:
                    if "consensus" in data:
                        command, index = data.split(" ")
                        index = int(index)
                        cli_command.handle_command(command, index, "", conn)
                    elif "set" in data:
                        command, index, word = data.split(" ")
                        index = int(index)
                        cli_command.handle_command(command, index, word, conn)
                    else:
                        cli_command.handle_command(data, 0, "", conn)
                else:
                    inputs.remove(source)
                    cli_connections.remove(source)
                    source.close()
        
        # check if it's time to send a new gossip message
        if time.time() >= next_gossip_time:
            process_command.reset_gossip()
            process_command.send_gossip()
            last_gossip_sent_time = time.time()

        # check for inactive peers and remove them
        current_time = time.time()
        for peer, last_gossip_time in list(last_gossip_times.items()):
            if current_time - last_gossip_time > TIMEOUT:
                process_command.remove_peer(peer)
                del last_gossip_times[peer]

                


    except KeyboardInterrupt as ki:
        print("User exited!")
        SOCKET.close
        sys.exit(0)

    except TimeoutError:
        pass