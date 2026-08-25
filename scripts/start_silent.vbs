Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\DJTU\HermesWorkspace\career-tracker"
WshShell.Run "D:\DJTU\HermesWorkspace\career-tracker\.venv\Scripts\pythonw.exe D:\DJTU\HermesWorkspace\career-tracker\backend\run_daemon.py", 0, False
