Set objXMLHTTP = CreateObject("MSXML2.XMLHTTP")
objXMLHTTP.open "GET", "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe", False
objXMLHTTP.setRequestHeader "User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

objXMLHTTP.send

If objXMLHTTP.Status = 200 Then
    Set objADOStream = CreateObject("ADODB.Stream")
    objADOStream.Open
    objADOStream.Type = 1
    objADOStream.Write objXMLHTTP.ResponseBody
    objADOStream.Position = 0
    objADOStream.SaveToFile "python_installer.exe", 2
    objADOStream.Close

    Set objShell = CreateObject("WScript.Shell")
    objShell.Run "python_installer.exe /quiet InstallAllUsers=1 PrependPath=1", 0, True

    ' Install Python dependencies (replace with appropriate command)
    objShell.Run "python -m pip install -r requirements.txt", 0, True

    ' Optional: Display a message upon successful installation
    objShell.Popup "Python and its dependencies have been installed silently.", 0, "Installation Complete"

    ' Clean up the temporary files
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    objFSO.DeleteFile "python_installer.exe"
End If
