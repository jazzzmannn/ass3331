"""
 Course:        COMP3331
 Term:          2022, T1
 Assignment:    1
 Description:   For creating a client

"""

# Libraries
import sys
from socket import *
from transmit import *
from os.path import exists

# Constants
USAGE_MESSAGE   = "Usage: python3 client.py server_IP_address server_port"
BUFFER_SIZE     = 1024
RETRANSMIT_COUNT = 3

# Main function
def main():
    
    # Check input
    if len(sys.argv) != 3 or not sys.argv[2].isdigit():
        print(USAGE_MESSAGE)
        exit(0)

    # Parse inputs
    serverAddress = sys.argv[1]
    serverPort = int(sys.argv[2])
    
    # Set up client socket
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    control = ClientControl(clientSocket, serverAddress, serverPort)
    control.run()
    
    # Close the socket
    clientSocket.close()

# Client Control class
class ClientControl():

    # Constructor
    def __init__(self, clientSocket, serverAddress, serverPort):
        self.clientSocket = clientSocket
        self.serverInformation = {
            "address": serverAddress,
            "port": serverPort,
            "name": "server"
        }
        self.username = "new client"
        self.udp = TransmitUDP(clientSocket, "", "", self.username)
        self.tcp = TransmitTCP(serverAddress, serverPort)
        self.loggedIn = False
    
    # Continually send messages to the server
    def run(self):

        # If not logged in, request login
        while not self.loggedIn:
            package = self.promptAuthentication()
            if package != None and package["command"] == CMD_EXIT[0]:
                return

        # Continually run
        while True:

            # Send command to the server
            commandString = getInput(self.username, "Enter a command (type HLP for available commands)")
            commandList = commandString.split(" ")
            command = commandList[0]
            arguments = " ".join(commandList[1:])

            # Send the command and retransmit if lost
            package = self.sendAndRetransmit(command, arguments)

            # Parse response
            if package != None and package["command"] == CMD_UPLOAD_FILE[0]:
                self.executeUpload(package)
            elif package != None and package["command"] == CMD_DOWNLOAD_FILE[0]:
                self.executeDownload(package)
            
            # Continue
            if package != None and package["command"] == CMD_EXIT[0]:
                break
    
    # Prompt authentication
    def promptAuthentication(self):

        # Send authentication request
        package = self.sendAndRetransmit(CMD_AUTHENTICATE[0], "")
        if package == None or package["command"] != CMD_USERNAME[0]:
            return package

        # Send username
        username = getInput(self.username)
        package = self.sendAndRetransmit(CMD_USERNAME[0], username)
        if package == None or package["status"] != STATUS_OK or package["command"] not in [CMD_LOGIN[0], CMD_REGISTER[0]]:
            return package
        
        # Send password
        password = getInput(self.username)
        package = self.sendAndRetransmit(package["command"], username + " " + password)
        if package == None or package["status"] == STATUS_OK:
            self.loggedIn = True
            self.username = username
            self.udp.name = username
    
    # Execute the upload
    def executeUpload(self, package):
        clientSocket = self.tcp.connectClient()
        self.tcp.sendFileTCP(package["content"], clientSocket)
        self.tcp.disconnect()
        displayContent(self.username, package["content"] + " has successfully been uploaded to the thread")

    # Execute the download
    def executeDownload(self, package):
        clientSocket = self.tcp.connectClient()
        self.tcp.receiveFileTCP(package["content"], clientSocket)
        self.tcp.disconnect()
        displayContent(self.username, package["content"] + " has successfully been downloaded from the thread")

    # Send and retransmit
    def sendAndRetransmit(self, command, content):

        # If upload/download command, check if the file exists
        if command == CMD_UPLOAD_FILE[0]:
            contentList = content.split(" ")
            if len(contentList) != 2:
                displayContent(self.username, "Usage: " + CMD_UPLOAD_FILE[1])
                return None
            elif not exists("./" + contentList[1]):
                displayContent(self.username, "The file, " + contentList[1] + ", does not exist")
                return None

        # Send the command 3 times or until a response is received
        for i in range(RETRANSMIT_COUNT):
            package = self.udp.sendUDP(command, content, STATUS_OK, self.serverInformation)
            package = self.udp.receiveUDP(RECV_MODE_TIMEOUT)
            if package == None:
                displayContent(self.username, "No response received, retransmitting ... (" + str(i+1) + "/" + str(RETRANSMIT_COUNT) + ")")
            else:
                break
        
        # If the package was lost/sent
        if package == None:
            displayContent(self.username, "The server did not respond, please try again")
        elif not package["command"] in [CMD_UPLOAD_FILE[0], CMD_DOWNLOAD_FILE[0]]:
            displayContent(self.username, package["content"])
        return package

# Main function caller
if __name__ == '__main__':
    main()