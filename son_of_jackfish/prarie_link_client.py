import win32com.client
import serial

if __name__ == "__main__":


    pl = win32com.client.Dispatch("PrairieLink.Application")
    pl.Connect()


    success = pl.SendScriptCommands("-Abort")
    print(success)
