### Test round trip communications (Serial -> CAN -> Serial)
  def testMessages(self):
      self.currentStatus.configure(text = "Testing Communication")
      try:
          num_loops = 50
          main_mod = serial.Serial(self.out_com.get(), baudrate = 115200, timeout = .03)
          main_mod.write("exit\r".encode()) #ensure this port is in correct mode for communication
          CAN = serial.Serial(self.can_com.get(), baudrate = 115200, timeout = .03)
          successes = 0
          for i in range(0, num_loops):
              # Send initial serial message
              main_mod.write(":S123N00ABCD00;".encode())
              # Recieve and verify incoming messages on other end
              CAN_recieve = readSerialWord(CAN)
              if(";" in CAN_recieve):
                  # If successful, write command back to original end
                  CAN.write(":S123N00ABCD00;".encode())
                  Ser_recieve = readSerialWord(main_mod)
                  if(";" in Ser_recieve):
                      # If recieved and verified, communication was successful
                      successes += 1
          CAN.close()
          main_mod.close()
          addTextToLabel(self.explanation, "\n\n"+str(successes)+"/"+str(num_loops)+" successes")
          # All communications must be successful
          if successes == num_loops:
              addTextToLabel(self.explanation, "\nSUCCESSFUL COMMUNICATION")
              return 0
          else:
              addTextToLabel(self.explanation, "\nFAILED COMMUNICATION")
              return 1

      except serial.SerialException as e:
          return self.getCOMProblem(e)
