import os.path
import os
import socket
import sys
import watchdog
import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import polling
from watchdog.events import PatternMatchingEventHandler
import logging
from random import random, choice
import string

FORMAT = 'utf-8'
# SIZE = 8192
# SIZE = 32767
# SIZE = 10000000
SIZE = 500000
END_LINE = os.linesep.encode(FORMAT)
WINDOWS_32 = 'win32'
IP = sys.argv[1]
PORT = sys.argv[2]
DIRECTORY = sys.argv[3]
TIMEOUT = sys.argv[4]
TASKS_FROM_SERVER = []
GOUST_PATH = '.goutputstream'
TIME_SLEEP_SEND = 0.1
EVENTS = []
SEPARATOR_WIN = '\\'
SEPARATOR_LINUX = '/'


class change:
    def __init__(self, src_path, action):
        self.src_path = src_path
        self.action = action


def is_serever_request(event):
    current = change(event.src_path, event.event_type)
    for c in TASKS_FROM_SERVER:
        if (c.src_path == current.src_path and c.action == current.action):
            TASKS_FROM_SERVER.remove(c)
            return True
    return False


def is_file_in_dir(event):
    time.sleep(2)
    if (os.path.exists(event.src_path)):
        return True
    return False


def on_any_event(event):
    if is_serever_request(event):
        return
    file_name_src = event.src_path[len(DIRECTORY) + 1:]
    if is_dir(file_name_src, event) and event.event_type == 'modified':
        pass
    else:
        EVENTS.append(event)
    if (file_name_src[-3:] == 'swp'):
        return
    if event.event_type == 'created':
        if (GOUST_PATH in file_name_src):
            return
        if sys.platform == WINDOWS_32:
            if not is_file_in_dir(event):
                return
        create_func(event, file_name_src)
        return
    elif event.event_type == 'deleted':
        if (GOUST_PATH in file_name_src):
            return
        deleted_func(event, file_name_src)
        return
    elif event.event_type == 'moved':
        file_name_dst = event.dest_path[len(DIRECTORY) + 1:]
        if (GOUST_PATH in file_name_src):
            moved_func(event, file_name_dst, file_name_dst)
            return
        # notice we look after the destination path
        moved_func(event, file_name_src, file_name_dst)
        return
    elif event.event_type == 'modified':
        if is_dir(file_name_src, event):
            return
        if (GOUST_PATH in file_name_src):
            return
        deleted_func(event, file_name_src)
        create_func(event, file_name_src)
        return


def moved_func(event, file_name_src, file_name_dest):
    # Event is created, you can process it now
    client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client1.connect((IP, int(PORT)))
    client = client1.makefile()
    time.sleep(TIME_SLEEP_SEND)
    client1.send(sys.platform.encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    operating_system_server = client.readline().strip()
    client1.send(b"moved" + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    client1.send(str(ID).encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    client1.send(str(NUM_OF_CLIENT).encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    client1.send(file_name_src.encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    client1.send(file_name_dest.encode(FORMAT) + END_LINE)
    if is_dir(file_name_src, event):
        client1.send(b"directory" + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
    else:
        client1.send(b"file" + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
    client.close()
    return


def random_id():
    return ''.join([choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(50)])


NUM_OF_CLIENT = random_id()
ID = 0


def operating_path(platform_source, path_source, separator=SEPARATOR_WIN):
    if platform_source != WINDOWS_32:
        separator = SEPARATOR_LINUX
    if os.sep != separator:
        path_source = path_source.replace(separator, os.sep)
    return path_source


def organize_files_for_sending(directory):
    list_dirs = []
    list_files = []
    # files
    for path, directories, files in os.walk(directory):
        for file1 in files:
            # checks if its in the main dir
            if path == directory:
                list_files.append(file1)
            # add the folder the file in it
            else:
                list_files.append(os.path.join(path[len(directory) + 1:], file1))
        sending_big_files(list_files, directory)
        if len(list_files) != 0:
            list_files.clear()
        # dirs
        for dir1 in directories:
            # checks if its in the main dir
            if path == directory:
                list_dirs.append(dir1)
            # add the folder the file in it
            else:
                list_dirs.append(os.path.join(path[len(directory) + 1:], dir1))
        make_dirs(list_dirs)

        if len(list_dirs) != 0:
            list_dirs.clear()
    # sending the files (not dir) to the server


def sending_big_files(list_files, directory):
    # checks if the list is empty
    if len(list_files) == 0:
        time.sleep(TIME_SLEEP_SEND)
        client1.send(b'done1' + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        return
    for file1 in list_files:
        file_size = str(os.path.getsize(os.path.join(directory, file1)))
        # sending file size
        client1.send(file_size.encode(FORMAT) + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        # sending file name (and path)
        client1.send(file1.encode(FORMAT) + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        f = open(os.path.join(directory, file1), 'rb')
        content = f.read(SIZE)
        # indicates the data deliverde already
        int_file_size = int(file_size)
        # if the file has no content
        if int_file_size == 0:
            client1.send(content)
            time.sleep(TIME_SLEEP_SEND)
            client1.send(b"done sending")
            time.sleep(TIME_SLEEP_SEND)
        else:
            while int_file_size > 0:
                client1.send(content)
                int_file_size -= SIZE
                time.sleep(TIME_SLEEP_SEND)
                try:
                    content = f.read(SIZE)
                    time.sleep(TIME_SLEEP_SEND)
                except:
                    time.sleep(TIME_SLEEP_SEND)
                    break
            time.sleep(TIME_SLEEP_SEND * 5)
            client1.send(b"done sending")
        f.close()
        # sending the content of the file - need to make proper function
        time.sleep(TIME_SLEEP_SEND * 2)
    # makes the server to wait until sending next packages - gets 'finish' - 6 letters
    client_accepted_files = client1.recv(6)
    time.sleep(TIME_SLEEP_SEND)
    client1.send(b'done1' + END_LINE)
    time.sleep(TIME_SLEEP_SEND)


def make_dirs(list_dirs):
    if len(list_dirs) == 0:
        time.sleep(TIME_SLEEP_SEND)
        client1.send(b'done2' + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        return
    for dir1 in list_dirs:
        client1.send((dir1 + os.linesep).encode(FORMAT))
        time.sleep(TIME_SLEEP_SEND)
    client1.send(b'done2' + END_LINE)
    time.sleep(TIME_SLEEP_SEND)


def create(client, client1, server_operation_system):
    data = client.readline().strip()
    if (data == 'file'):
        file_size = str(client.readline()).strip()
        # receiving files
        file_name = client.readline().strip()
        file_name = operating_path(server_operation_system, file_name)
        TASKS_FROM_SERVER.append(change(os.path.join(DIRECTORY, file_name), "created"))
        recive_files(os.path.join(DIRECTORY, file_name), client1)
    elif (data == 'directory'):
        # making dirs
        data = client.readline().strip()
        data = operating_path(server_operation_system, data)
        TASKS_FROM_SERVER.append(change(os.path.join(DIRECTORY, data), "created"))
        os.makedirs(os.path.join(DIRECTORY, data))


class OnMyWatch:
    def run(self, ID):
        patterns = ["*"]
        ignore_patterns = None
        ignore_directories = False
        case_sensitive = False
        my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
        my_event_handler.on_any_event = on_any_event
        go_recursively = True
        my_observer = polling.PollingObserver()
        my_observer.schedule(my_event_handler, DIRECTORY, recursive=go_recursively)
        my_observer.start()
        while True:
            time.sleep(int(TIMEOUT))
            client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            time.sleep(TIME_SLEEP_SEND)
            client1.connect((IP, int(PORT)))
            client = client1.makefile()
            time.sleep(TIME_SLEEP_SEND)
            client1.send(sys.platform.encode(FORMAT) + END_LINE)
            time.sleep(TIME_SLEEP_SEND)
            operating_system_server = client.readline().strip()
            client1.send(b"pull" + END_LINE)
            time.sleep(TIME_SLEEP_SEND)
            client1.send(ID.encode(FORMAT) + END_LINE)
            time.sleep(TIME_SLEEP_SEND)
            client1.send(str(NUM_OF_CLIENT).encode(FORMAT) + END_LINE)
            time.sleep(TIME_SLEEP_SEND)
            data = client.readline().strip()
            if data == '':
                client1.close()
                continue
            while data != 'DONE':
                if (data == 'created'):
                    create(client, client1, operating_system_server)
                elif (data == 'deleted'):
                    data = client.readline().strip()
                    if (data == 'directory'):
                        data_to_delete = client.readline().strip()
                        data_to_delete = operating_path(operating_system_server, data_to_delete)
                        TASKS_FROM_SERVER.append(change(os.path.join(DIRECTORY, data_to_delete), "deleted"))
                        delete_whole_dir(os.path.join(DIRECTORY, data_to_delete))
                    if (data == 'file'):
                        data_to_delete = client.readline().strip()
                        data_to_delete = operating_path(operating_system_server, data_to_delete)
                        TASKS_FROM_SERVER.append(change(os.path.join(DIRECTORY, data_to_delete), "deleted"))
                        try:
                            os.remove(os.path.join(DIRECTORY, data_to_delete))
                        except:
                            continue
                # NEED TO CHANGE HERE THE IMPLEMENTATION
                elif (data == 'moved'):
                    src_path = client.readline().strip()
                    src_path = operating_path(operating_system_server, src_path)
                    src_path = os.path.join(DIRECTORY, src_path)
                    dest_path = client.readline().strip()
                    dest_path = operating_path(operating_system_server, dest_path)
                    dest_path = os.path.join(DIRECTORY, dest_path)
                    if not os.path.exists(src_path) and os.path.exists(dest_path):
                        file_or_dir = client.readline().strip()
                        continue

                    # TASKS_FROM_SERVER.append(dest_path)
                    file_or_dir = client.readline().strip()
                    if not os.path.exists(src_path) and not os.path.exists(dest_path):
                        if (file_or_dir == 'directory'):
                            os.makedirs(dest_path)
                        elif (file_or_dir == 'file'):
                            f = open(dest_path, 'wb')
                            f.close()
                        TASKS_FROM_SERVER.append(change(dest_path, "created"))
                    else:
                        if (file_or_dir == 'directory'):
                            delete_whole_dir(src_path)
                            if not (os.path.exists(dest_path)):
                                os.makedirs(dest_path)
                        if (file_or_dir == 'file'):
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            os.replace(src_path, dest_path)
                        TASKS_FROM_SERVER.append(change(src_path, "moved"))
                data = client.readline().strip()
            time.sleep(TIME_SLEEP_SEND)
            client1.close()
            time.sleep(TIME_SLEEP_SEND)
        self.observer.join()


def delete_whole_dir(path1):
    list_of_dirs = [path1]
    for path, directories, files in os.walk(path1):
        for file1 in files:
            os.remove(os.path.join(path, file1))
        for dir1 in directories:
            list_of_dirs.append(os.path.join(path, dir1))
    list_len = len(list_of_dirs)
    for i in range(list_len):
        if os.path.exists(list_of_dirs[list_len - (1 + i)]):
            os.rmdir(list_of_dirs.pop())
        else:
            list_of_dirs.pop()


def checks_if_tasks_from_server(event, change):
    if len(TASKS_FROM_SERVER) == 0:
        return False
    if (event.event_type == 'moved'):
        TASKS_FROM_SERVER.pop(0)
        if len(TASKS_FROM_SERVER):
            TASKS_FROM_SERVER.pop(0)
        return True
    if (TASKS_FROM_SERVER[0] == event.src_path):
        TASKS_FROM_SERVER.pop(0)
        return True
    return False


def is_dir(file_name_src, event):
    if sys.platform == WINDOWS_32:
        if '.' in file_name_src:
            return False
        else:
            return True
    else:
        if event.is_directory:
            return True
        return False


def modified_over_again():
    if len(EVENTS) < 2:
        return False
    path = EVENTS[len(EVENTS) - 1].src_path
    count = 0
    for e in EVENTS[-1:]:
        if e.event_type == 'deleted' and e.src_path == path:
            count = count + 1
    # check if it appear more than once
    if count >= 1:
        EVENTS.clear()
        return True
    return False


def create_func(event, file_name):
    # Event is created, you can process it now
    client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client1.connect((IP, int(PORT)))
    client = client1.makefile()
    time.sleep(TIME_SLEEP_SEND)
    client1.send(sys.platform.encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    operating_system_server = client.readline().strip()
    client1.send(b"created" + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    client1.send(str(ID).encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    client1.send(str(NUM_OF_CLIENT).encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    if is_dir(file_name, event):
        client1.send(b"directory" + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        client1.send(file_name.encode(FORMAT) + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
    else:
        client1.send(b"file" + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        file_size = str(os.path.getsize(os.path.join(DIRECTORY, file_name)))
        client1.send(file_size.encode(FORMAT) + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        client1.send(file_name.encode(FORMAT) + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        int_file_size = int(file_size)
        count = 0
        f = open(os.path.join(DIRECTORY, file_name), 'rb')
        content = f.read()
        # if the file has no content
        if (int_file_size == 0):
            client1.send(content)
            time.sleep(TIME_SLEEP_SEND)
        else:
            while (int_file_size > 0):
                client1.send(content[count:SIZE + count])
                count += (SIZE + 1)
                int_file_size -= SIZE
                time.sleep(TIME_SLEEP_SEND)
        f.close()
        time.sleep(TIME_SLEEP_SEND * 5)
        client1.send(b'done sending')
        time.sleep(TIME_SLEEP_SEND)
        client_accepted_files = client1.recv(6)
    client.close()
    return


def deleted_func(event, file_name):
    # Event is modified, you can process it now
    client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client1.connect((IP, int(PORT)))
    client = client1.makefile()
    time.sleep(TIME_SLEEP_SEND)
    client1.send(sys.platform.encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    operating_system_server = client.readline().strip()
    client1.send(b"deleted" + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    client1.send(str(ID).encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    client1.send(str(NUM_OF_CLIENT).encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    if is_dir(file_name, event):
        client1.send(b"directory" + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
    else:
        client1.send(b"file" + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
    client1.send(file_name.encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    client.close()
    return


def start_watchdog(ID):
    watch = OnMyWatch()
    watch.run(ID)


def recive_files(path, client_socket1):
    data_to_write = b""
    data_from_sender = client_socket1.recv(SIZE)
    while (data_from_sender != b'done sending') and (data_from_sender != b""):
        data_to_write += data_from_sender
        data_from_sender = client_socket1.recv(SIZE)
    try:
        f = open(path, 'wb')
        f.write(data_to_write)
        f.close()
    except:
        pass
    client_socket1.send(b'finish')
    time.sleep(TIME_SLEEP_SEND)


client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client1.connect((IP, int(PORT)))
with client1:
    client = client1.makefile(mode="rb")

time.sleep(TIME_SLEEP_SEND)
client1.send(sys.platform.encode(FORMAT) + END_LINE)
operating_system_server = client.readline().strip().decode(FORMAT)
# dont have id
if len(sys.argv) == 5:
    client1.send(b'new client' + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    ID = client.readline().strip().decode(FORMAT)
    client1.send(NUM_OF_CLIENT.encode(FORMAT) + END_LINE)
    organize_files_for_sending(DIRECTORY)
    client1.send(b'DONE' + END_LINE)
else:
    ID = sys.argv[5]
    client1.send(b'old client' + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    # sending client id
    client1.send(str(ID).encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    # sending client num
    client1.send(NUM_OF_CLIENT.encode(FORMAT) + END_LINE)
    time.sleep(TIME_SLEEP_SEND)
    # create new folder - name folder - DIRECTORY
    os.makedirs(DIRECTORY)
    data = client.readline().strip().decode(FORMAT)
    while data != 'DONE':
        # receiving files
        while data != 'done1':
            if data == "":
                continue
            try:
                file_size = int(data)
            except:
                continue
            file_name = client.readline().strip().decode(FORMAT)
            file_name = operating_path(operating_system_server, file_name)
            recive_files(os.path.join(DIRECTORY, file_name), client1)
            data = client.readline().strip().decode(FORMAT)
            # making dirs
        data = client.readline().strip().decode(FORMAT)
        while data != 'done2':
            dir_exist = True
            data = operating_path(operating_system_server, data)
            while dir_exist:
                if os.path.exists(os.path.join(DIRECTORY, data)):
                    data = client.readline()
                    data = operating_path(operating_system_server, data)
                else:
                    dir_exist = False
            os.makedirs(os.path.join(DIRECTORY, data))
            data = client.readline().strip().decode(FORMAT)
        data = client.readline().strip().decode(FORMAT)
    time.sleep(TIME_SLEEP_SEND)
client.close()
start_watchdog(ID)
