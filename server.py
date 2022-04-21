"""
 Course:        COMP3331
 Term:          2022, T1
 Assignment:    1
 Description:   For creating a server

"""

# Libraries
import sys
from socket import * 
from fileIO import *
from threading import Thread
from authenticate import *
from transmit import *
from os.path import exists

# Constants
USAGE_MESSAGE   = "Usage: python3 server.py server_port"
SERVER_HOST     = "127.0.0.1"
ACCEPT_INTERVAL = 1

# Main function
def main():
    
    # Check input
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print(USAGE_MESSAGE)
        exit(0)
    serverAddress = SERVER_HOST
    serverPort = int(sys.argv[1])

    # Set up client socket
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind((serverAddress, serverPort))
    print("[server] Socket bound, IP=" + str(SERVER_HOST) + ", PORT=" + str(serverPort))
    print("[server] Waiting for clients ...")

    # Initialise
    safeWrite(ACTIVE_USERS_FILE, "", "w") # truncate
    safeWrite(FORUM_FILE_LIST, "", "w") # truncate

    # Set up controller for server
    control = ServerControl(serverSocket, serverAddress, serverPort)
    try:
        control.run()
    except KeyboardInterrupt:
        removeAllFiles()
        safeRemove(ACTIVE_USERS_FILE)
        safeRemove(FORUM_FILE_LIST)

    # Close the socket
    serverSocket.close()
    print("[server] Server has shutdown")

# Controller for the server
class ServerControl():

    # Constructor
    def __init__(self, serverSocket, serverAddress, serverPort):
        self.udp = TransmitUDP(serverSocket, serverAddress, serverPort, "server", True)
        self.tcp = TransmitTCP(serverAddress, serverPort)
        self.auth = Authenticate()

    # Run the client thread
    def run(self):

        # Continually run
        while True:

            # Wait for request
            package = None
            while package == None:
                package = self.udp.receiveUDP(RECV_MODE_QUICK)
            self.auth.updateCredentials()

            # Handle requests from client
            handler = Handler(package, self.udp, self.tcp, self.auth)
            handler.start()

# For handling client requests
class Handler(Thread):

    # Constructor
    def __init__(self, package, udp, tcp, auth):
        Thread.__init__(self)
        self.command = package["command"]
        self.content = package["content"]
        self.sender = package["sender"]
        self.udp = udp
        self.tcp = tcp
        self.auth = auth

    # Execute code based on the command
    def run(self):
        if self.command == CMD_AUTHENTICATE[0]:
            self.processAuthentication()
        elif self.command == CMD_USERNAME[0]:
            self.processUsername()
        elif self.command == CMD_LOGIN[0]:
            self.processLogin()
        elif self.command == CMD_REGISTER[0]:
            self.processRegister()
        elif self.command == CMD_CREATE_THREAD[0]:
            self.processCreateThread()
        elif self.command == CMD_POST_MESSAGE[0]:
            self.processPostMessage()
        elif self.command == CMD_DELETE_MESSAGE[0]:
            self.processDeleteMessage()
        elif self.command == CMD_EDIT_MESSAGE[0]:
            self.processEditMessage()
        elif self.command == CMD_LIST_THREADS[0]:
            self.processListThreads()
        elif self.command == CMD_READ_THREAD[0]:
            self.processReadThread()
        elif self.command == CMD_REMOVE_THREAD[0]:
            self.processRemoveThread()
        elif self.command == CMD_UPLOAD_FILE[0]:
            self.processUploadFile()
        elif self.command == CMD_DOWNLOAD_FILE[0]:
            self.processDownloadFile()
        elif self.command == CMD_EXIT[0]:
            self.processTerminate()
        elif self.command == CMD_HELP[0]:
            self.processHelp()
        else:
            self.processUnknown()

    # Process authentication request
    def processAuthentication(self):
        self.udp.sendUDP(CMD_USERNAME[0], "Enter your username", STATUS_OK, self.sender)

    # Process the username
    def processUsername(self):
        username = self.content

        # Check username validity
        if not self.auth.isValid(username):
            self.udp.sendUDP(CMD_DISPLAY[0], "The username is invalid, please try again", STATUS_BAD, self.sender)
        
        # If username exist, login (if not already)
        elif self.auth.doesUsernameExist(username):
            if self.auth.isLoggedIn(username):
                self.udp.sendUDP(CMD_DISPLAY[0], "The account is already logged in, please try again", STATUS_BAD, self.sender)
            else:
                self.udp.sendUDP(CMD_LOGIN[0], "Enter your password", STATUS_OK, self.sender)
        
        # If username does not exist, register
        else:
            self.udp.sendUDP(CMD_REGISTER[0], "Enter your password", STATUS_OK, self.sender)

    # Process login
    def processLogin(self):
        usernamePassword = self.content.split(" ")

        # Check number of arguments
        if len(usernamePassword) != 2:
            self.udp.sendUDP(CMD_DISPLAY[0], "The password is invalid, please try again", STATUS_BAD, self.sender)
            return

        # Check password validity
        username, password = usernamePassword[0], usernamePassword[1]
        if not self.auth.isValid(password):
            self.udp.sendUDP(CMD_DISPLAY[0], "The password is invalid, please try again", STATUS_BAD, self.sender)
        
        # If username and password match
        elif self.auth.doesUsernamePasswordMatch(username, password):
            self.auth.logUserIn(username)
            self.udp.sendUDP(CMD_DISPLAY[0], "You have successfully logged in as " + username, STATUS_OK, self.sender)
        
        # Otherwise, error
        else:
            self.udp.sendUDP(CMD_DISPLAY[0], "The username and password do not match, please try again", STATUS_BAD, self.sender)

    # Process registration
    def processRegister(self):
        usernamePassword = self.content.split(" ")

        # Check number of arguments
        if len(usernamePassword) != 2:
            self.udp.sendUDP(CMD_DISPLAY[0], "The password is invalid, please try again", STATUS_BAD, self.sender)
            return

        # Check password validity
        username, password = usernamePassword[0], usernamePassword[1]
        if not self.auth.isValid(password):
            self.udp.sendUDP(CMD_DISPLAY[0], "The password is invalid, please try again", STATUS_BAD, self.sender)
        
        # Password is valid, register and login
        else:
            self.auth.addUser(username, password)
            self.auth.logUserIn(username)
            self.udp.sendUDP(CMD_DISPLAY[0], "You have successfully registered and logged in as " + username, STATUS_OK, self.sender)

    # Process thread creation
    def processCreateThread(self):
        argumentList = self.content.split(" ")
        
        # Check number of arguments
        if len(argumentList) != 1 or argumentList[0] == "":
            self.udp.sendUDP(CMD_DISPLAY[0], "Usage: " + CMD_CREATE_THREAD[1], STATUS_BAD, self.sender)
            return
        
        # Check validity of filename
        threadTitle = argumentList[0]
        if not isFilenameValid(threadTitle) or exists("./" + threadTitle + ".txt") or threadTitle + ".txt" in getFileList():
            self.udp.sendUDP(CMD_DISPLAY[0], "The thread title is either invalid or already exists", STATUS_BAD, self.sender)
        
        # Everything is fine, so create thread
        else:
            safeWrite(threadTitle + ".txt", self.sender["name"] + "\n", "w")
            addFilename(threadTitle + ".txt")
            self.udp.sendUDP(CMD_DISPLAY[0], "The thread, " + threadTitle + ", has been successfully created", STATUS_OK, self.sender)

    # Process message posting
    def processPostMessage(self):
        argumentList = self.content.split(" ")

        # Check number of arguments
        if len(argumentList) <= 1:
            self.udp.sendUDP(CMD_DISPLAY[0], "Usage: " + CMD_POST_MESSAGE[1], STATUS_BAD, self.sender)
            return
        
        # Check existence of filename
        threadTitle = argumentList[0]
        content = " ".join(argumentList[1:])
        if not threadTitle + ".txt" in getFileList():
            self.udp.sendUDP(CMD_DISPLAY[0], "The thread title does not exist", STATUS_BAD, self.sender)
            return
        
        # Add the message
        addMessage(threadTitle, self.sender["name"], content)
        self.udp.sendUDP(CMD_DISPLAY[0], "The message has been successfully added to " + threadTitle, STATUS_OK, self.sender)
    
    # Process message deletion
    def processDeleteMessage(self):
        argumentList = self.content.split(" ")

        # Check number of arguments
        if len(argumentList) != 2 or not argumentList[1].isdigit():
            self.udp.sendUDP(CMD_DISPLAY[0], "Usage: " + CMD_DELETE_MESSAGE[1], STATUS_BAD, self.sender)
            return

        # Check existence of filename
        threadTitle = argumentList[0]
        messageNumber = int(argumentList[1])
        if not threadTitle + ".txt" in getFileList():
            self.udp.sendUDP(CMD_DISPLAY[0], "The thread title does not exist", STATUS_BAD, self.sender)
            return
        
        # Remove the message
        result = deleteMessage(threadTitle, self.sender["name"], messageNumber)
        self.udp.sendUDP(CMD_DISPLAY[0], result, STATUS_OK, self.sender)
    
    # Process message editing
    def processEditMessage(self):
        argumentList = self.content.split(" ")

        # Check number of arguments
        if len(argumentList) <= 2 or not argumentList[1].isdigit():
            self.udp.sendUDP(CMD_DISPLAY[0], "Usage: " + CMD_EDIT_MESSAGE[1], STATUS_BAD, self.sender)
            return
        
        # Check existence of filename
        threadTitle = argumentList[0]
        messageNumber = int(argumentList[1])
        content = " ".join(argumentList[2:])
        if not threadTitle + ".txt" in getFileList():
            self.udp.sendUDP(CMD_DISPLAY[0], "The thread title does not exist", STATUS_BAD, self.sender)
            return
        
        # Edit content of message
        result = editMessage(threadTitle, self.sender["name"], messageNumber, content)
        self.udp.sendUDP(CMD_DISPLAY[0], result, STATUS_OK, self.sender)

    # Process thread listing
    def processListThreads(self):

        # Get all files
        fileList = [file[:-4] for file in getFileList() if file.endswith(".txt")]
        
        # If no files
        if len(fileList) == 0:
            self.udp.sendUDP(CMD_DISPLAY[0], "There are currently no active threads", STATUS_BAD, self.sender)
        
        # Otherwise, show them
        else:
            toWrite = "There are currently " + str(len(fileList)) + " active threads:\n  "
            toWrite += "\n  ".join(fileList)
            self.udp.sendUDP(CMD_DISPLAY[0], toWrite, STATUS_OK, self.sender)

    # Process thread reading
    def processReadThread(self):
        argumentList = self.content.split(" ")

        # Check number of arguments
        if len(argumentList) != 1:
            self.udp.sendUDP(CMD_DISPLAY[0], "Usage: " + CMD_READ_THREAD[1], STATUS_BAD, self.sender)
            return
        
        # Check existence of filename
        threadTitle = argumentList[0]
        if not threadTitle + ".txt" in getFileList():
            self.udp.sendUDP(CMD_DISPLAY[0], "The thread title does not exist", STATUS_BAD, self.sender)
            return
        
        # Read content of file
        toWrite = "Reading thread, " + threadTitle + ":\n  "
        toWrite += "\n  ".join(fileToLineList(threadTitle))
        self.udp.sendUDP(CMD_DISPLAY[0], toWrite, STATUS_OK, self.sender)
    
    # Process thread removal
    def processRemoveThread(self):
        argumentList = self.content.split(" ")

        # Check number of arguments
        if len(argumentList) != 1:
            self.udp.sendUDP(CMD_DISPLAY[0], "Usage: " + CMD_REMOVE_THREAD[1], STATUS_BAD, self.sender)
            return

        # Check existence of filename
        threadTitle = argumentList[0]
        if not threadTitle + ".txt" in getFileList():
            self.udp.sendUDP(CMD_DISPLAY[0], "The thread title does not exist", STATUS_BAD, self.sender)
            return
        
        # Check authorship of thread
        creator, _ = fileToThread(threadTitle)
        if creator != self.sender["name"]:
            self.udp.sendUDP(CMD_DISPLAY[0], "You are not the creator of this thread", STATUS_BAD, self.sender)
            return
        
        # Remove file
        safeRemove("./" + threadTitle + ".txt")
        removeFilename(threadTitle + ".txt")
        self.udp.sendUDP(CMD_DISPLAY[0], "The thread, " + threadTitle + ", has been successfully removed", STATUS_OK, self.sender)

    # Process file upload
    def processUploadFile(self):
        argumentList = self.content.split(" ")

        # Check number of arguments
        if len(argumentList) != 2:
            self.udp.sendUDP(CMD_DISPLAY[0], "Usage: " + CMD_UPLOAD_FILE[1], STATUS_BAD, self.sender)
            return
        
        # Check validity of filename
        threadTitle = argumentList[0]
        filename = argumentList[1]
        if not isFilenameValid(filename):
            self.udp.sendUDP(CMD_DISPLAY[0], "The filename is invalid", STATUS_BAD, self.sender)
        
        # Check existence of thread
        elif not threadTitle + ".txt" in getFileList():
            self.udp.sendUDP(CMD_DISPLAY[0], "The thread title does not exist", STATUS_BAD, self.sender)
        
        # Check if file already uploaded
        elif isFileUploaded(threadTitle, filename):
            self.udp.sendUDP(CMD_DISPLAY[0], filename + " has already been uploaded to the thread", STATUS_BAD, self.sender)

        # Otherwise, upload
        else:
            self.udp.sendUDP(CMD_UPLOAD_FILE[0], filename, STATUS_OK, self.sender)
            addFileToThread(threadTitle, self.sender["name"], filename)
            addFilename(threadTitle + "-" + filename)
            clientSocket = self.tcp.connectServer()
            self.tcp.receiveFileTCP(threadTitle + "-" + filename, clientSocket)
            self.tcp.disconnect()

    # Process file download
    def processDownloadFile(self):
        argumentList = self.content.split(" ")

        # Check number of arguments
        if len(argumentList) != 2:
            self.udp.sendUDP(CMD_DISPLAY[0], "Usage: " + CMD_UPLOAD_FILE[1], STATUS_BAD, self.sender)
            return
        
        # Check validity of filename
        threadTitle = argumentList[0]
        filename = argumentList[1]
        if not isFilenameValid(filename):
            self.udp.sendUDP(CMD_DISPLAY[0], "The filename is invalid", STATUS_BAD, self.sender)
        
        # Check existence of thread
        elif not threadTitle + ".txt" in getFileList():
            self.udp.sendUDP(CMD_DISPLAY[0], "The thread title does not exist", STATUS_BAD, self.sender)
        
        # Check if file already uploaded
        elif not isFileUploaded(threadTitle, filename):
            self.udp.sendUDP(CMD_DISPLAY[0], filename + " has not been uploaded to the thread", STATUS_BAD, self.sender)
        
        # Otherwise, download
        else:
            self.udp.sendUDP(CMD_DOWNLOAD_FILE[0], filename, STATUS_OK, self.sender)
            clientSocket = self.tcp.connectServer()
            self.tcp.sendFileTCP(threadTitle + "-" + filename, clientSocket)
            self.tcp.disconnect()

    # Process termination request
    def processTerminate(self):
        disconnectMessage = self.sender["name"] + " has disconnected from the server"
        displayContent("server", disconnectMessage)
        self.auth.logUserOut(self.sender["name"])
        self.udp.sendUDP(CMD_EXIT[0], disconnectMessage, STATUS_OK, self.sender)
    
    # Process help request
    def processHelp(self):

        # All commands
        commandList = [
            CMD_HELP, CMD_CREATE_THREAD, CMD_POST_MESSAGE, CMD_DELETE_MESSAGE,
            CMD_EDIT_MESSAGE, CMD_LIST_THREADS, CMD_READ_THREAD, CMD_UPLOAD_FILE,
            CMD_DOWNLOAD_FILE, CMD_REMOVE_THREAD, CMD_EXIT
        ]
        commandListString = "The following are a list of available commands:\n"
        
        # Display all command information
        for command in commandList:
            commandListString += "  " + command[0] + ", Usage: " + command[1] + " (" + command[2] + ")" + "\n"
        self.udp.sendUDP(CMD_DISPLAY[0], commandListString[:-1], STATUS_OK, self.sender)
    
    # Process unknown request
    def processUnknown(self):
        self.udp.sendUDP(CMD_DISPLAY[0], self.command + " is not a command", STATUS_BAD, self.sender)

# Main function caller
if __name__ == '__main__':
    main()