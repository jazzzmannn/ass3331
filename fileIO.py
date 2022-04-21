"""
 Course:        COMP3331
 Term:          2022, T1
 Assignment:    1
 Description:   For interacting with threads

"""

# Imports
from os import remove

# Constants
THREAD_TYPE_MESSAGE = "message"
THREAD_TYPE_FILE = "file"
FORUM_FILE_LIST = "forumFileList.txt"

# For storing information about threads created and files uploaded
def addFilename(filename):
    safeWrite(FORUM_FILE_LIST, filename + "\n", "a")

# For getting the list of files added/uploaded
def getFileList():
    try:
        f = open(FORUM_FILE_LIST, "r")
        fileList = f.read().splitlines()
        f.close()
    except:
        fileList = []
    return fileList

# For removing a file from the list of files added/uploaded
def removeFilename(filename):
    fileList = getFileList()
    fileList.remove(filename)
    safeWrite(FORUM_FILE_LIST, "", "w") # truncate
    for file in fileList:
        safeWrite(FORUM_FILE_LIST, file + "\n", "a")

# Remove all .txt files
def removeAllFiles():
    fileList = getFileList()
    for file in fileList:
        safeRemove("./" + file)
    safeWrite(FORUM_FILE_LIST, "", "w") # truncate

# Converts an existing thread into a list of lines
def fileToLineList(threadTitle):
    f = open(threadTitle + ".txt", "r")
    threadContent = f.read().splitlines()
    f.close()
    return threadContent

# Converts an existing thread into its components
def fileToThread(threadTitle):
    threadContent = fileToLineList(threadTitle)

    # Get author and messages    
    creator = threadContent[0]
    threadList = []
    for threadLine in threadContent[1:]:
        threadLineList = threadLine.split(" ")

        # For messagez
        if threadLineList[0].isdigit():
            threadLineDict = {
                "type": THREAD_TYPE_MESSAGE,
                "number": threadLineList[0],
                "author": threadLineList[1][:-1],
                "content": " ".join(threadLineList[2:])
            }
        
        # For file uploads
        else:
            threadLineDict = {
                "type": THREAD_TYPE_FILE,
                "username": threadLineList[0],
                "filename": threadLineList[2]
            }
        threadList.append(threadLineDict)
    
    # Return
    return creator, threadList

# Converts the components of a thread to text
def threadToFile(threadTitle, creator, threadList):
    toWrite = creator + "\n"
    messageNumber = 1
    for i in range(len(threadList)):

        # For messages
        if threadList[i]["type"] == THREAD_TYPE_MESSAGE:
            toWrite += str(messageNumber) + " " + threadList[i]["author"] + ": " + threadList[i]["content"] + "\n"
            messageNumber += 1
        elif threadList[i]["type"] == THREAD_TYPE_FILE:
            toWrite += threadList[i]["username"] + " uploaded " + threadList[i]["filename"] + "\n"
    
    # Safely write
    safeWrite(threadTitle + ".txt", toWrite, "w")

# Adds a message
def addMessage(threadTitle, author, content):
    _, threadList = fileToThread(threadTitle)
    numMessages = sum([1 for threadLine in threadList if threadLine["type"] == THREAD_TYPE_MESSAGE])
    messageLine = str(numMessages + 1) + " " + author + ": " + content + "\n"
    safeWrite(threadTitle + ".txt", messageLine, "a")

# Adds a file upload line
def addFileToThread(threadTitle, author, filename):
    safeWrite(threadTitle + ".txt", author + " uploaded " + filename + "\n", "a")

# Get index of message number
def getMessageIndex(threadList, messageNumber):
    for i in range(len(threadList)):
        if threadList[i]["type"] == THREAD_TYPE_MESSAGE and threadList[i]["number"] == str(messageNumber):
            return i
    return -1

# Deletes a message
def deleteMessage(threadTitle, author, messageNumber):
    creator, threadList = fileToThread(threadTitle)

    # Check message number
    numMessages = sum([1 for threadLine in threadList if threadLine["type"] == THREAD_TYPE_MESSAGE])
    if messageNumber > numMessages or messageNumber <= 0:
        return "The message number does not exist"
    
    # Check authorship
    index = getMessageIndex(threadList, messageNumber)
    if index == -1 or author != threadList[index]["author"]:
        return "You are not the author of this message"
    
    # Remove the message
    threadList.pop(index)
    threadToFile(threadTitle, creator, threadList)
    return "The message has been successfully deleted from " + threadTitle

# Edits a message
def editMessage(threadTitle, author, messageNumber, content):
    creator, threadList = fileToThread(threadTitle)

    # Check message number
    numMessages = sum([1 for threadLine in threadList if threadLine["type"] == THREAD_TYPE_MESSAGE])
    if messageNumber > numMessages or messageNumber <= 0:
        return "The message number does not exist"

    # Check authorship
    index = getMessageIndex(threadList, messageNumber)
    if index == -1 or author != threadList[index]["author"]:
        return "You are not the author of this message"
    
    # Edit message
    threadList[index]["content"] = content
    threadToFile(threadTitle, creator, threadList)
    return "The message has been successfully edited in " + threadTitle

# Checks whether a file has already been uploaded to a file
def isFileUploaded(threadTitle, filename):
    _, threadList = fileToThread(threadTitle)
    for threadLine in threadList:
        if threadLine["type"] == THREAD_TYPE_FILE and threadLine["filename"] == filename:
            return True
    return False

# Safe remove
def safeRemove(filename):
    try:
        remove(filename)
    except:
        pass

# Checks whether a filename is valid
def isFilenameValid(filename):
    if len(filename) > 100:
        return False
    valid = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890()_-,."
    for character in filename:
        if character not in valid:
            return False
    return True

# Safely writes to a file TODO
def safeWrite(filename, content="", mode="w"):
    f = open(filename, mode)
    f.write(content)
    f.close()