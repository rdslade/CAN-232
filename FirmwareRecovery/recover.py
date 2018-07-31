import serial
import time
from xmodem import XMODEM, ACK
import os
import logging
import re

version = ""
type = ""
firmwareFiles = []
startTime = 0

def exitWithMessage(message):
    print("\n" + message)
    print("\nFailed program completed in " + str(round(time.time() - startTime, 2)) + " seconds")
    input("\nPress enter to exit")
    exit()

def readSerialWord(ser_port):
    char = '0'
    response = ""
    # Continue reading word until not more chars
    while char != '':
        char = ser_port.read().decode()
        response += char
    return response

def pressButton(ser_port, command):
    time.sleep(1)
    ser_port.write(command.encode())
    time.sleep(1)

def enterConfigMode(ser_port, verbose = True):
    global type
    startTime = time.time()
    response = ""
    if verbose:
        print("Entering config mode...")
    while "#0#" not in response:
        pressButton(ser_port, configCommand)
        ser_port.write("\n\r".encode())
        response = readSerialWord(ser_port)
        if time.time() - startTime > 10:
            exitWithMessage("TIMED OUT WAITING FOR BUTTON")
    if "SLAVE #0#" in response:
        type = "slave"
    elif "MASTER #0#" in response:
        type = "master"
    else:
        exitWithMessage("COULD NOT DETERMINE CONFIGURATION OF DEVICE")

def getSerNum(ser_port):
    ser_port.write("get sernum\r".encode())
    sernumStr = readSerialWord(ser_port)
    sernumArr = sernumStr.split()
    startIndex = 9999
    endIndex = 9999
    startString = "<A:"
    endString = ">"
    sernumActual = []
    for portion in sernumArr:
        curIndex = sernumArr.index(portion)
        if startString in portion:
            startIndex = curIndex
        if endString in portion:
            endIndex = curIndex

        if curIndex >= startIndex and curIndex <= endIndex :
            sernumActual.append(portion)

    adjustedBegin = sernumActual[0].split(startString)[1]
    adjustedEnd = sernumActual[len(sernumActual) - 1].split(endString)[0]
    sernumActual[0] = adjustedBegin
    sernumActual[len(sernumActual) - 1] = adjustedEnd

    sernumStr = ""
    for portion in sernumActual:
        sernumStr += str(portion)
    print("Serial number: " + sernumStr + " [" + type + "]")
    return sernumActual


def exitConfigMode(ser_port, verbose = True):
    ser_port.write("exit\r".encode())
    if verbose:
        print("\nExited config mode")

def readUntil(char = None):
    def serialPortReader():
        while True:
            tmp = ser.read(1).decode()
            if not tmp or (char and char == tmp):
                break
            yield tmp
    return ''.join(serialPortReader())

def getc(size, timeout=1):
    char = ser.read(size)
    return char

def putc(data, timeout=1):
    ser.write(data)
    time.sleep(0.001) # give device time to send ACK

def setupDownload(ser_port, numArr):
    pot = "firmware download "
    for num in numArr:
        pot += str(num) + " "
    pot += "\r\n"
    readyResponse = ""
    print("\nConfiguring for XMODEM transfer...")
    while "Start XMODEM send" not in readyResponse:
        ser_port.write(pot.encode())
        readyResponse = readSerialWord(ser_port)
    # readUntil(ACK)
    print("Ready for XMODEM send")
    #print("PLEASE CYCLE POWER TO THE MODULE")
def getVersionNumber(filename):
    fileNameArr = filename.split("-")
    for i in range(0, len(fileNameArr)):
        try:
            int(fileNameArr[i])
            v = fileNameArr[i] + "." + fileNameArr[i + 1]
            return v
        except:
            pass

def performDownload(ser_port):
    global type, version
    modem = XMODEM(getc, putc)
    modem.log.disabled = True

    for file in firmwareFiles:
        if type in file:
            filename = file
            version = getVersionNumber(filename)
            if not re.match(r"\d{1,}[.]\d{1,}[A-z]", version):
                exitWithMessage("CAN'T DETERMINE VERSION FROM FILE NAME")

    f = open(filename, 'rb')
    # readyResponse = ""
    # while "Begin XMODEM download now" not in readyResponse:
    #     ser_port.write(" ".encode())
    #     readyResponse = readSerialWord(ser_port)
    success = False
    while not success:
        print("\nLoading firmware...")
        success = modem.send(f, quiet = 1)
    print("Successful load!")
    modem.log.disabled = False

def checkVersion(ser_port):
    print("\nVerifying firmware...")
    enterConfigMode(ser_port, verbose = False)
    ser_port.write("get version\r".encode())
    response = ""
    str = "Version "
    while response == "":
        response = readSerialWord(ser_port)
    if version in response:
        str += version + " loaded with "
    else:
        exitWithMessage("WRONG VERSION LOADED")
    ser_port.write("\r\n".encode())
    response = readSerialWord(ser_port)
    if type.upper() in response:
        str += type + " configuration"
        print(str)
    else:
        exitWithMessage("WRONG CONFIGURATION LOADED")
    exitConfigMode(ser_port, verbose = False)


def checkFirmwareFiles():
    os.chdir("Firmware")
    firmwareFiles = os.listdir()
    if len(firmwareFiles) > 2:
        exitWithMessage("TOO MANY FIRMWARE FILES")
    return firmwareFiles

def setBaudFlush(ser_port, baud):
    ser_port.flush()
    ser_port.baudrate = baud

if __name__ == "__main__":
    com = input("Enter the COM port: ")
    configCommand = "!!!"
    try:
        ser = serial.Serial(com, baudrate = 19200, timeout = .1)
    except serial.SerialException as e:
        exitWithMessage("SERIAL ERROR: COULD NOT OPEN '" + com + "'")
    firmwareFiles = checkFirmwareFiles()

    again = "Y"
    counter = 0
    while again in ["Y", "y", "yes", "Yes"]:
        counter += 1
        print("\nModule " + str(counter))
        startTime = time.time()
        setBaudFlush(ser, 19200)
        enterConfigMode(ser)
        sernum = getSerNum(ser)
        setupDownload(ser, sernum)
        setBaudFlush(ser, 115200)
        performDownload(ser)
        time.sleep(2)
        setBaudFlush(ser, 19200)
        checkVersion(ser) # NOT NEEDED/WORKING YET
        print("\nSuccessful program completed in " + str(round(time.time() - startTime, 2)) + " seconds")
        again = input("\nLoad another? (Y or N): ")
