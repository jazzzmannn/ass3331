"""
 Course:        COMP3331
 Term:          2022, T1
 Assignment:    1
 Description:   For sending and receiving data

"""

# Imports
from socket import *
import json, select, time

# Constants
BUFFER_SIZE         = 2048
RECV_TIMEOUT        = 1 # seconds
RECV_RATE           = 0.1 # limits the receival rate
RECV_MODE_TIMEOUT   = "timeout"
RECV_MODE_QUICK     = "quick"

# Commands
CMD_INITIATE        = ["INT"]
CMD_DISPLAY         = ["DSP"]
CMD_AUTHENTICATE    = ["ATH"]
CMD_USERNAME        = ["USR"]
CMD_LOGIN           = ["LGN"]
CMD_REGISTER        = ["RGT"]
CMD_HELP            = ["HLP", "HLP", "list available commands"]
CMD_CREATE_THREAD   = ["CRT", "CRT threadTitle", "create a thread"]
CMD_POST_MESSAGE    = ["MSG", "MSG threadTitle message", "post a message"]
CMD_DELETE_MESSAGE  = ["DLT", "DLT threadTitle messageNumber", "delete a message"]
CMD_EDIT_MESSAGE    = ["EDT", "EDT threadTitle messageNumber message", "edit a message"]
CMD_LIST_THREADS    = ["LST", "LST", "list all the available threads"]
CMD_READ_THREAD     = ["RDT", "RDT threadTitle", "read a thread"]
CMD_UPLOAD_FILE     = ["UPD", "UPD threadTitle filename", "upload a file"]
CMD_DOWNLOAD_FILE   = ["DWN", "DWN threadTitle filename", "download a file"]
CMD_REMOVE_THREAD   = ["RMV", "RMV threadTitle", "remove a thread"]
CMD_EXIT            = ["XIT", "XIT", "terminate a client session"]

# Possible statuses
STATUS_OK   = "OK"
STATUS_BAD  = "BAD"
STATUS_LOST = "LOST"

# For transmitting data over UDP (assumes that sockets are already bounded)
class TransmitUDP():

    # Constructor
    def __init__(self, socket, address, port, name, display=False):
        self.socket = socket
        self.address = address
        self.port = port
        self.name = name
        self.display = display
    
    # Send UDP
    def sendUDP(self, command, content, status, receiver):
        
        # Prepare the package
        package = {
            "command": command,
            "content": content,
            "status": status,
            "sender": {
                "address": self.address,
                "port": self.port,
                "name": self.name
            }
        }
        packageString = str(package).replace("'", '"')

        # Display meta data
        if self.display:
            print("[" + self.name + " >> " + str(receiver["name"]) + "] " + command + " " + status)

        # Send the package
        self.socket.sendto(packageString.encode(), (receiver["address"], receiver["port"]))
    
    # Receive UDP
    def receiveUDP(self, mode=RECV_MODE_TIMEOUT):

        # With a timeout
        if mode == RECV_MODE_TIMEOUT:
            self.socket.setblocking(0)
            ready = select.select([self.socket], [], [], RECV_TIMEOUT)
            try:
                if ready:
                    packageString, senderAddress = self.socket.recvfrom(BUFFER_SIZE)
            except BlockingIOError:
                return None
        
        # Without a timeout
        elif mode == RECV_MODE_QUICK:
            self.socket.setblocking(0)
            try:
                packageString, senderAddress = self.socket.recvfrom(BUFFER_SIZE)
            except BlockingIOError:
                time.sleep(RECV_RATE)
                return None

        # Load the packet (string to dict)
        package = json.loads(packageString.decode())

        # Update sender information
        package["sender"]["address"] = senderAddress[0]
        package["sender"]["port"] = senderAddress[1]
        
        # Display meta data
        if self.display:
            print("[" + self.name + " << " + str(package["sender"]["name"]) + "] " + package["command"] + " " + package["status"])

        # Return package
        return package

# For transmitting data over TCP
class TransmitTCP():
    
    # Constructor
    def __init__(self, serverAddress, serverPort):
        self.serverAddress = serverAddress
        self.serverPort = serverPort
    
    # Connect server to TCP link
    def connectServer(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((self.serverAddress, self.serverPort))
        self.socket.listen()
        clientSocket, _ = self.socket.accept()
        return clientSocket
    
    # Connect client to TCP link
    def connectClient(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((self.serverAddress, self.serverPort))
        return self.socket

    # Send data
    def sendFileTCP(self, filename, clientSocket):
        f = open(filename, "rb")
        fileData = f.read(BUFFER_SIZE)
        while fileData:
            clientSocket.send(fileData)
            fileData = f.read(BUFFER_SIZE)
        f.close()

    # Receive data
    def receiveFileTCP(self, filename, clientSocket):
        f = open(filename, "wb")
        while True:
            fileData = clientSocket.recv(BUFFER_SIZE)
            f.write(fileData)
            if len(fileData) < BUFFER_SIZE:
                break
        f.close()

    # Disconnect server from TCP link
    def disconnect(self):
        self.socket.close()

# Display content of package to console
def displayContent(name, content):
    contentList = content.split("\n")
    for contentLine in contentList:
        print("[" + name + "] " + contentLine)

# Prompts input from the console
def getInput(name, content=""):
    if content != "":
        displayContent(name, content)
    return input("[" + name + "] ")