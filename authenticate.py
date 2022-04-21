"""
 Course:        COMP3331
 Term:          2022, T1
 Assignment:    1
 Description:   For interacting with the credentials file

"""

# Imports
from fileIO import *

# Constants
ACTIVE_USERS_FILE = "activeUsers.txt"
CREDENTIALS_FILE = "credentials.txt"

# Authenticate class
class Authenticate():

    # Constructor
    def __init__(self):
        self.updateCredentials()
    
    # Updates the credentials as a list of dictionaries
    def updateCredentials(self):

        # Read all data
        f = open(CREDENTIALS_FILE, "r")
        userStringList = f.read().splitlines()

        # Put data in list of dictionaries
        userDictList = []
        for userString in userStringList:
            user = userString.split()
            userDict = {
                "username": user[0],
                "password": user[1]
            }
            userDictList.append(userDict)
        
        # Close and return
        f.close()
        self.userDictList = userDictList
        return userDictList

    # Checks whether a username / password is valid
    def isValid(self, usernamePassword):
        if len(usernamePassword) == 0:
            return False
        valid = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*_-+=`|\(){}[]:;\"'<>,.?/"
        for character in usernamePassword:
            if character not in valid:
                return False
        return True

    # Checks whether a username exists
    def doesUsernameExist(self, username):
        for userDict in self.userDictList:
            if username == userDict["username"]:
                return True
        return False

    # Checks whether a username and password match
    def doesUsernamePasswordMatch(self, username, password):
        for userDict in self.userDictList:
            if username == userDict["username"]:
                return password == userDict["password"]
        return False

    # Logs a user in
    def logUserIn(self, username):
        if self.isLoggedIn(username):
            return
        safeWrite(ACTIVE_USERS_FILE, username + "\n", "a")

    # Logs a user out
    def logUserOut(self, username):
        if not self.isLoggedIn(username):
            return
        activeUserList = self.getActiveUsers()
        activeUserList.remove(username)
        toWrite = ""
        for user in activeUserList:
            toWrite += user + "\n"
        safeWrite(ACTIVE_USERS_FILE, toWrite, "w")

    # Checks whether a user is logged in
    def isLoggedIn(self, username):
        for user in self.getActiveUsers():
            if user == username:
                return True
        return False

    # Read from active user list
    def getActiveUsers(self):
        try:
            f = open(ACTIVE_USERS_FILE, "r")
            activeUserList = f.read().splitlines()
            f.close()
        except:
            activeUserList = []
        return activeUserList

    # Adds a user to the list of credentials
    def addUser(self, username, password):
        
        # Update local credentials list
        self.updateCredentials()
        self.userDictList.append({"username": username, "password": password})

        # Prepare new credentials list
        toWrite = ""
        for userDict in self.userDictList:
            toWrite += userDict["username"] + " " + userDict["password"] + "\n"

        # Write to the credentials file
        safeWrite(CREDENTIALS_FILE, toWrite, "w")