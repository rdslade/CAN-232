import serial
import time
from xmodem import XMODEM, ACK
import os
import logging

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

def enterConfigMode(ser_port):
    global type
    startTime = time.time()
    response = ""
    while response == "":
        pressButton(ser, configCommand)
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

    return sernumActual


def exitConfigMode(ser_port):
    ser_port.write("exit\r".encode())

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
    while "Start XMODEM send" not in readyResponse:
        ser_port.write(pot.encode())
        readyResponse = readSerialWord(ser_port)
    # readUntil(ACK)
    ser_port.baudrate = 115200
    #print("PLEASE CYCLE POWER TO THE MODULE")

def performDownload(ser_port):
    global type
    modem = XMODEM(getc, putc)
    modem.log.disabled = True

    for file in firmwareFiles:
        if type in file:
            filename = file

    f = open(filename, 'rb')
    # readyResponse = ""
    # while "Begin XMODEM download now" not in readyResponse:
    #     ser_port.write(" ".encode())
    #     readyResponse = readSerialWord(ser_port)
    print("\nLoading firmware...")
    success = False
    while not success:
        success = modem.send(f, quiet = 1)
    print("Successful load!")
    modem.log.disabled = False

def checkFirmwareFiles():
    os.chdir("Firmware")
    firmwareFiles = os.listdir()
    if len(firmwareFiles) > 2:
        exitWithMessage("TOO MANY FIRMWARE FILES")
    return firmwareFiles

if __name__ == "__main__":
    startTime = time.time()
    com = input("Enter the COM port: ")
    # mode = sys.argv[1]
    # if mode == "normal":
    #     baud = 115200
    #     configCommand = ":CONFIG;"
    # elif mode == "raymond":
    baud = 19200
    configCommand = "!!!"
    try:
        ser = serial.Serial(com, baudrate = baud, timeout = .1)
    except serial.SerialException as e:
        exitWithMessage("SERIAL ERROR: COULD NOT OPEN '" + com + "'")
    firmwareFiles = checkFirmwareFiles()
    try:
        enterConfigMode(ser)
    except:
        enterConfigMode(ser)
    sernum = getSerNum(ser)
    setupDownload(ser, sernum)
    performDownload(ser)
    # statinfo = os.stat(r"Firmware\raymond-download-2-00C-" + type + ".image")
    # print(statinfo.st_size)
    # if time.time() - startTime < 15:
    #     performDownload(ser)
    exitConfigMode(ser)
    print("\nSuccessful program completed in " + str(round(time.time() - startTime, 2)) + " seconds")
    x = input("\nPress enter to exit")
