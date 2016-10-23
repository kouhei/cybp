# -*- coding: utf-8 -*-

import sys
import socket
import threading

def server_loop(localhost, localport, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((localhost, localport))
    except:
        print("[!!] Failed to listen on %s:%d" % (localhost, localport))
        print("[!!] Check for other listening sockets or correct permissions")
        sys.exit()
    
    print("[*] Listening on %s:%d" % (localhost, localport))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        #show connect information from local host
        print("[==>] Received incoming connection from %s:%d" % (addr[0], addr[1]))

        #start thread to connect to remote_host
        proxy_thread = threading.Thread(
                target=proxy_handler,
                args=(client_socket,remote_host,remote_port,receive_first))
        proxy_thread.start()

def main():
    #read commandline arguments
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport] [remote_host] [remote_port] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    
    #local host setting to receive transmission
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    #setting to remote
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    #setting whether or not to receive data before submit it to remote host
    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    #start socket to wait connections
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    #connect to remote host
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    #if need , receive data from remote host
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

        #give data to function processing received data
        remote_buffer = response_handler(remote_buffer)

        #if exist data to submit to local host
        if len(remote_buffer):
            print("[<==] Sending %d bytes to localhost." % len(remote_buffer))
            client_socket.send(remote_buffer)
            
    #start loop to repeat receiving data from localhost, submitting data to remote host and submitting to local host
    while True:
        #receive data from local host
        local_buffer = receive_from(client_socket)

        if len(local_buffer):
            print("[==>] Received %d bytes from localhost." % len(local_buffer))
            hexdump(local_buffer)

            #give data to function processing submitting data
            local_buffer = request_handler(local_buffer)

            #submit data to remote host
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        #receive response
        remote_buffer = receive_from(remote_socket)

        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)

            #give data to function processing received data
            remote_buffer = response_handler(remote_buffer)

            #submit response data to local host
            client_socket.send(remote_buffer)
            print("[<==] Sent to localhost.")
            # if don't come data from remote host or local host, close connection
            if not len(local_buffer) or not len(remote_buffer):
                client_socket.close()
                remote_socket.close()
                print("[*] No more data. Closing connections.")
                break

main()
