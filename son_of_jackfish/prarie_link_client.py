import win32com.client

if __name__ == "__main__":
    pl = win32com.client.Dispatch("PrarieLink.Application")
    # pl = win32com.client.Dispatch("PrarieLink64.Application")

    pl.Connect("128.32.173.1")
    success = pl.SendScriptCommands("-Abort")
    print(success)
