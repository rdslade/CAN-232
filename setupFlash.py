import os

cwd = os.getcwd()

changeFolder = cwd + r"\CANUSB_Flash"
os.chdir(changeFolder)

for i in range(1, 11):
    newFileName = "CANUSB_Flash" + str(i) + ".bat"
    with open(newFileName, "w+") as file:
        file.write('cd "C:\Program Files (x86)\Flash Magic"\n')
        file.write('FM.exe @' + cwd + "\CANUSB_Config\CANUSB_CommandFile" + str(i) + ".txt");

    
    


#cd "C:\Program Files (x86)\Flash Magic"

#FM.exe @c:\Users\Julia\Desktop\GridConnect\LabUpdate\CAN-232\CANUSB_Config\CANUSB_CommandFile1.txt
