

   ____ _                 _   ____  _                 _       _             
  / ___| | ___  _   _  __| | / ___|(_)_ __ ___  _   _| | __ _| |_ ___  _ __ 
 | |   | |/ _ \| | | |/ _` | \___ \| | '_ ` _ \| | | | |/ _` | __/ _ \| '__|
 | |___| | (_) | |_| | (_| |  ___) | | | | | | | |_| | | (_| | || (_) | |   
  \____|_|\___/ \__,_|\__,_| |____/|_|_| |_| |_|\__,_|_|\__,_|\__\___/|_|   
                                                                            

                                                                              


A client-server, TCP based, file transfer algorithm that maintains constantly updated folders on different computers, built using Python's WatchDog library. The program "links" end-users together and keeps the end-users' folders as if it was a cloud system that is constantly updated and can be accessed from anywhere.  The logic of the program uses "manual ACKs" that were added to seperate parts of the process and maintain an order of commands executed.

![Cloud-Server](https://user-images.githubusercontent.com/84729141/186115962-f223efd7-78b2-4341-bbe8-3c9a14e25777.jpeg)

To run the code first run server.py with args, then run client.py with their args. 

Server: Argument: 	

1 - Port number (for example 12345).

Client: Arguments: 	

1 - IP - the server IP.

2 - Port - the server port.

3 - dir path - the dir to backup in the cloud server.

4 - TIMEOUT - indicates the time to sync for changes.

5 - ID - If it's an existing client from another connection - you need to insert his unique ID.

*Side Note:The code is a bit messy (not modular) because the instructor's demand was to upload only client and server files

https://user-images.githubusercontent.com/84729141/164456881-eeb0a037-dae9-4c93-98e1-0d554d80d8b0.mp4

