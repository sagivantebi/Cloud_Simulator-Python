import os
import socket
import string
import sys
from random import random, choice
import time

WINDOWS_32 = 'win32'
FORMAT = 'utf-8'
SIZE = 500000
ABS_PATH_SERVER_CLOUD = os.getcwd()
END_LINE = os.linesep.encode(FORMAT)
NUM_PORT = sys.argv[1]
TIME_SLEEP_SEND = 0.1
SEPARATOR_WIN = '\\'
SEPARATOR_LINUX = '/'


def main():
    if len(sys.argv) != 2:
        return
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', int(NUM_PORT)))
    # max number of client to wait
    server.listen(300)
    dict_of_id = {}
    for path, directories, files in os.walk(ABS_PATH_SERVER_CLOUD):
        for dir1 in directories:
            dict_of_id[dir1] = os.path.join(ABS_PATH_SERVER_CLOUD, dir1)
        break
    changes = {}
    while True:
        # indicates if the client is new or not for the connect line
        new_client = True
        client_socket1, client_address = server.accept()
        with client_socket1:
            client_socket = client_socket1.makefile(mode="rb")
        operating_system_client = client_socket.readline().strip().decode(FORMAT)
        # sending the system operation
        client_socket1.sendall(sys.platform.encode(FORMAT) + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        data = client_socket.readline().strip().decode(FORMAT)
        if data == "new client":
            users = {}
            idInUse = True
            client_id = random_id()
            # CHECK HERE IF THE CLIENT ID IS ALREADY IN USE IN THE DICT
            while idInUse:
                if client_id not in dict_of_id.keys():
                    idInUse = False
                client_id = random_id()
            # send the id to the client
            print(str(client_id))
            client_socket1.sendall(client_id.encode(FORMAT) + END_LINE)
            time.sleep(TIME_SLEEP_SEND)
            client_num = client_socket.readline().strip().decode(FORMAT)
            # create new folder - name folder - id
            os.makedirs(os.path.join(ABS_PATH_SERVER_CLOUD, str(client_id)))
            # path to the client folder
            dict_of_id[client_id] = os.path.join(ABS_PATH_SERVER_CLOUD, str(client_id))
            users[client_num] = []
            changes[client_id] = users
            data = client_socket.readline().strip().decode(FORMAT)
            while data != 'DONE':
                # receiving files
                while data != 'done1':
                    if data == "":
                        continue
                    try:
                        file_size = int(data)
                    except:
                        continue
                    file_name = client_socket.readline().strip().decode(FORMAT)
                    file_name = operating_path(operating_system_client, file_name)
                    recive_files(os.path.join(dict_of_id[client_id], file_name), client_socket1)
                    data = client_socket.readline().strip().decode(FORMAT)
                # making dirs
                data = client_socket.readline().strip().decode(FORMAT)
                while data != 'done2':
                    dir_exist = True
                    data = operating_path(operating_system_client, data)
                    while dir_exist:
                        if os.path.exists(os.path.join(dict_of_id[client_id], data)):
                            data = client_socket.readline().strip().decode(FORMAT)
                            data = operating_path(operating_system_client, data)
                        else:
                            dir_exist = False
                    os.makedirs(os.path.join(dict_of_id[client_id], data))
                    data = client_socket.readline().strip().decode(FORMAT)
                data = client_socket.readline().strip().decode(FORMAT)
        elif (data == "old client"):
            client_id = client_socket.readline().strip().decode(FORMAT)
            directory = dict_of_id[client_id]
            client_num = client_socket.readline().strip().decode(FORMAT)
            changes[client_id][client_num] = []
            # creating the logging client his dir in his pc (sending him the folder)
            organize_files(directory, client_socket, client_socket1)
            time.sleep(TIME_SLEEP_SEND)
            client_socket1.sendall(b'DONE' + END_LINE)
            time.sleep(TIME_SLEEP_SEND)
        # recving changes form the client
        elif data == 'pull':
            client_id = client_socket.readline().strip().decode(FORMAT)
            client_num = client_socket.readline().strip().decode(FORMAT)
            if len(changes[client_id][client_num]):
                for i in (changes[client_id][client_num]):
                    # if the i is a byte format already
                    try:
                        client_socket1.send(i.encode(FORMAT) + END_LINE)
                    except:
                        try:
                            package_size = int(len(i))
                            count = 0
                            while package_size >= 0:
                                client_socket1.send(i[count:SIZE + count])
                                count += SIZE
                                package_size -= SIZE
                                time.sleep(TIME_SLEEP_SEND)
                            time.sleep(TIME_SLEEP_SEND*5)
                            client_socket1.send(b'done sending')
                            time.sleep(TIME_SLEEP_SEND)
                            client_accepted_files = client_socket1.recv(6)
                        except:
                            continue
                    time.sleep(TIME_SLEEP_SEND*2)
                changes[client_id][client_num].clear()
            time.sleep(TIME_SLEEP_SEND)
            client_socket1.send(b'DONE' + END_LINE)
            time.sleep(TIME_SLEEP_SEND)
            client_socket1.close()
            continue
        elif data == 'created':
            create_call(client_socket, client_socket1, dict_of_id, changes, operating_system_client)
        elif data == 'deleted':
            delete_call(client_socket, dict_of_id, changes, operating_system_client)
        elif data == 'moved':
            moved_call(client_socket, dict_of_id, changes, operating_system_client)
        client_socket1.close()


def moved_call(client_socket, dict_of_id, changes, operating_system_client):
    list_of_changes = []
    list_of_changes.append("moved")
    client_id = client_socket.readline().strip().decode(FORMAT)
    client_num = client_socket.readline().strip().decode(FORMAT)
    src_path = client_socket.readline().strip().decode(FORMAT)
    src_path = operating_path(operating_system_client, src_path)
    list_of_changes.append(src_path)
    src_path = os.path.join(dict_of_id[client_id], src_path)
    dest_path = client_socket.readline().strip().decode(FORMAT)
    dest_path = operating_path(operating_system_client, dest_path)
    list_of_changes.append(dest_path)
    dest_path = os.path.join(dict_of_id[client_id], dest_path)
    if not os.path.exists(src_path) and os.path.exists(dest_path):
        return
    file_or_dir = client_socket.readline().strip().decode(FORMAT)
    list_of_changes.append(file_or_dir)
    if not os.path.exists(src_path) and not os.path.exists(dest_path):
        if (file_or_dir == 'directory'):
            os.makedirs(dest_path)
        elif (file_or_dir == 'file'):
            f = open(dest_path, 'wb')
            f.close()
    elif (file_or_dir == 'directory'):
        delete_whole_dir(src_path)
        if not (os.path.exists(dest_path)):
            os.makedirs(dest_path)
    elif (file_or_dir == 'file'):
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        os.replace(src_path, dest_path)
    for key in changes[client_id]:
        if key != client_num:
            for i in range(len(list_of_changes)):
                changes[client_id][key].append(list_of_changes[i])


def delete_call(client_socket, dict_of_id, changes, operating_system_client):
    exsist_file = True
    list_of_changes = []
    list_of_changes.append("deleted")
    client_id = client_socket.readline().strip().decode(FORMAT)
    client_num = client_socket.readline().strip().decode(FORMAT)
    data = client_socket.readline().strip().decode(FORMAT)
    if data == 'directory':
        list_of_changes.append("directory")
        data_to_delete = client_socket.readline().strip().decode(FORMAT)
        data_to_delete = operating_path(operating_system_client, data_to_delete)
        list_of_changes.append(data_to_delete)
        if os.path.exists(os.path.join(dict_of_id[client_id], data_to_delete)):
            delete_whole_dir(os.path.join(dict_of_id[client_id], data_to_delete))
        else:
            exsist_file = False
    if data == 'file':
        list_of_changes.append("file")
        data_to_delete = client_socket.readline().strip().decode(FORMAT)
        data_to_delete = operating_path(operating_system_client, data_to_delete)
        list_of_changes.append(data_to_delete)
        if os.path.exists(os.path.join(dict_of_id[client_id], data_to_delete)):
            os.remove(os.path.join(dict_of_id[client_id], data_to_delete))
        else:
            exsist_file = False
    if exsist_file:
        for key in changes[client_id]:
            if key != client_num:
                for i in range(len(list_of_changes)):
                    changes[client_id][key].append(list_of_changes[i])


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


def create_call(client_socket, client_socket1, dict_of_id, changes, operating_system_client):
    client_id = client_socket.readline().strip().decode(FORMAT)
    time.sleep(TIME_SLEEP_SEND)
    client_num = client_socket.readline().strip().decode(FORMAT)
    data = client_socket.readline().strip().decode(FORMAT)
    exsist_file = False
    list_of_changes = []
    list_of_changes.append("created")
    if data == 'directory':
        list_of_changes.append("directory")
        data = client_socket.readline().strip().decode(FORMAT)
        data = operating_path(operating_system_client, data)
        if os.path.exists(os.path.join(dict_of_id[client_id], data)):
            exsist_file = True
        else:
            os.makedirs(os.path.join(dict_of_id[client_id], data))
            list_of_changes.append(data)
    elif data == 'file':
        list_of_changes.append("file")
        data = client_socket.readline().strip().decode(FORMAT)
        # receiving files
        file_size = str(data)
        file_name = client_socket.readline().strip().decode(FORMAT)
        file_name = operating_path(operating_system_client, file_name)
        list_of_changes.append(file_size)
        list_of_changes.append(file_name)
        if (os.path.exists(os.path.join(dict_of_id[client_id], file_name))):
            exsist_file = True
        else:
            # path = os.path.join(dict_of_id[client_id], file_name)
            # os.makedirs(os.path.dirname(path), exist_ok=True)
            # list_of_changes.append(os.path.dirname(path)[len(dict_of_id[client_id]) + 1:])
            list_of_changes.append(
                recive_files(os.path.join(dict_of_id[client_id], file_name), client_socket1))
    if not exsist_file:
        for key in changes[client_id]:
            if key != client_num:
                for i in range(len(list_of_changes)):
                    changes[client_id][key].append(list_of_changes[i])


def random_id():
    return ''.join([choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(128)])


def organize_files(directory, client_socket, client_socket1):
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
        sending_big_files(list_files, directory, client_socket1)
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
        make_dirs(list_dirs, client_socket, client_socket1)

        if len(list_dirs) != 0:
            list_dirs.clear()
    # sending the files (not dir) to the server


def sending_big_files(list_files, directory, client1):
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


def recive_files(path, client_socket1):
    data_to_write = b''
    data_from_sender = client_socket1.recv(SIZE)
    while (data_from_sender != b'done sending') and (data_from_sender != b''):
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
    return data_to_write


def make_dirs(list_dirs, client_socket, client_socket1):
    if len(list_dirs) == 0:
        time.sleep(TIME_SLEEP_SEND)
        client_socket1.send(b'done2' + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
        return
    for dir1 in list_dirs:
        client_socket1.send(dir1.encode(FORMAT) + END_LINE)
        time.sleep(TIME_SLEEP_SEND)
    client_socket1.send(b'done2' + END_LINE)
    time.sleep(TIME_SLEEP_SEND)


def operating_path(platform_source, path_source, separator=SEPARATOR_WIN):
    if platform_source != WINDOWS_32:
        separator = SEPARATOR_LINUX
    if os.sep != separator:
        path_source = path_source.replace(separator, os.sep)
    return path_source


if __name__ == '__main__':
    main()
