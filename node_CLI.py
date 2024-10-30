import cmd
import json
import socket
import sys

HOST = ''
PORT = 15000

if __name__ == '__main__':
    SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    SOCKET.connect(HOST, PORT)
    print(f"CLI connected successful to Hung Lu Dao peer: {(HOST, PORT)}")

    command = input("\r\nEnter command: ")
    
    SOCKET.sendall(command.encode())
    data = SOCKET.recv(1024)
    print(f"Received: {data.decode("utf-8")}")
    SOCKET.close()
    

