#!/usr/bin/env python3

import socket
import sys
import os

from file_reader import FileReader
import select

class Jewel:

    def __init__(self, port, file_path, file_reader):
        self.file_path = file_path
        self.file_reader = file_reader

        #print("Program is started print")
        #sys.stdout.write("Program has started")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))

        s.listen(5) #The number of new connections allowed before reusing connections
        inputs = [ s ]
        address_Lookup = {}
        # if you need to look for new connections and determine where to read, select can do that
        while True: #Replace true w select over sockets in the read vector
            reads, writes, execepts = select.select(inputs, [], [], 0.5)
            if(len(reads) == 0):
                continue
    
            for i in range(len(reads)):
                if(reads[i] == s):
                    (client, address) = s.accept()
                    port_Number = client.getpeername()[1]
                    sys.stdout.write('[CONN] Connection from ' + str(address[0]) + ' on port ' + str(port_Number) + '\n')
                    inputs.append(client)
                    address_Lookup[client] = address #saves the address
                else:
                    client = reads[i]
                    address = address_Lookup[client]
                    port_Number = client.getpeername()[1]
                    data = client.recv(1024).decode('utf-8')

                    if not data:
                        continue
                    
                    header_end = data.find('\r\n\r\n')
                    if(header_end == -1):
                        #Malformed request
                        errorRequest = 'HTTP/1.1 400 Bad Request\r\n'.encode('utf-8')
                        client.send(errorRequest) 
                        continue
                    if header_end > -1:
                        header_string = data[:header_end]
                        lines = header_string.split('\r\n')

                        request_fields = lines[0].split()
                        #print(request_fields)
                        headers = lines[1:]

                        header_lookup = {}

                        for header in headers:
                            header_fields = header.split(':')
                            key = header_fields[0].strip()
                            val = header_fields[1].strip()
                            header_lookup[key] = val
                            #print(key + ' : ' + val)

                        request_alternate_val = header_lookup.get('Access-Control-Request-Method')
                        #print("The alternate value is: " + request_alternate_val)
                        #This is necessary for handling PostMan requests, since their request is an OPTIONS type but subspecifies the true type
                        #POSTMAN SUCKS. WORKS IF YOU JUST GO TO THE ADDRESS DIRECTLY VIA LOCALHOST ADDRESS
                        if(request_alternate_val != None):
                            if(request_fields[0] != request_alternate_val):
                                request_fields[0] = request_alternate_val

                        print('[REQU] [' + str(address[0]) + ':' + str(port_Number)  + '] ' + request_fields[0] + ' request for ' + request_fields[1])
                        
                        #Parsing time! Woooooh! So much fun!!!!
                        cookies = header_lookup.get('Cookie')#Returns None if not in the request
                        connection_status = header_lookup.get('Connection')
                        #content_type = header_lookup.get('Content-Type')
                        path_to_append = request_fields[1]
                        if(path_to_append[0] == '/'):
                            path_to_append = path_to_append[1:]
                        path_to_pass = os.path.join(file_path, path_to_append)
                        #print("Path that will be passed to filereader: " + path_to_pass)

                        filepath_split = request_fields[1].split('/') #Look at content type
                        #print(filepath_split)
                        supported = False
                        supported_types = []
                        supported_types.extend(['html', 'css', 'png','jpg','gif','txt'])
                        for i in range(len(supported_types)):
                            if(supported_types[i] in filepath_split[-1]):
                                #print(filepath_split[-1])
                                supported = True
                            if(file_reader.head(path_to_pass, cookies) != None and '.' not in filepath_split[-1]):
                                supported = True #If its not another filetype and it has a file size, then
                        sendback = file_reader.head(path_to_pass, cookies)
                        if(sendback == None):
                                #print("Head request returned None")
                                #Do I need to do something different for a request
                                message = 'HTTP/1.1 404 Not Found\r\n\r\n'.encode('utf-8')
                                client.send(message)
                                inputs.remove(client)
                                client.close()
                                print('[ERRO] [' + str(address[0]) + ':' + str(port_Number) + '] ' + request_fields[0] + ' returned error ' + '404')
                                continue
                        if(supported == True):
                            #if(content_type not in {'text/html','text/css','image/png','image/jpeg','image/gif'}):
                            if('html' in filepath_split[-1]):
                                content_type = 'text/html'
                            elif('txt' in filepath_split[-1]):
                                content_type = 'text/plain'
                            elif('css' in filepath_split[-1]):
                                content_type = 'text/css'
                            elif('png' in filepath_split[-1]):
                                content_type = 'image/png'
                            elif('jpg' in filepath_split[-1]):
                                content_type = 'image/jpeg'
                            elif('gif' in filepath_split[-1]):
                                content_type = 'image/gif'
                            else:
                                content_type = 'text/html' #
                        else:
                            #Not supported, then tell it that we haven't implemented yet
                            sendback = 'HTTP/1.1 501 Method Unimplemented\r\n\r\n'.encode('utf-8')
                            #print("Not Supported, aka Supported Failed")
                            print('[ERRO] [' + str(address[0]) + ':' + str(port_Number) + '] ' + request_fields[0] + ' returned error ' + '501')
                            client.send(sendback)
                            inputs.remove(client)
                            client.close()
                            continue

                        if(request_fields[0] not in {'GET', 'HEAD'}):
                            sendback = 'HTTP/1.1 501 Method Unimplemented\r\n\r\n'.encode('utf-8')
                            #print("Invalid Request Type")
                            print('[ERRO] [' + str(address[0]) + ':' + str(port_Number) + '] ' + request_fields[0] + ' returned error ' + '501')
                            client.send(sendback)
                            inputs.remove(client)
                            client.close()
                            continue

                        #Request type not head or get, return HTTP 501 not implemented
                    
                        if(request_fields[0] == 'HEAD'):
                            sendback = file_reader.head(path_to_pass, cookies)
                            if(sendback == None):
                                #print("Head request returned None")
                                #Do I need to do something different for a request
                                message = 'HTTP/1.1 404 Not Found\r\n\r\n'.encode('utf-8')
                                client.send(message)
                                inputs.remove(client)
                                client.close()
                                print('[ERRO] [' + str(address[0]) + ':' + str(port_Number) + '] ' + request_fields[0] + ' returned error ' + '404')
                                continue
                            message = 'HTTP/1.1 200 OK\r\nServer: rah9eu\r\nContent-Length: ' + str(sendback) + '\r\nContent-Type: ' + content_type + '\r\n\r\n'
                            client.send(message.encode('utf-8'))
                            inputs.remove(client)
                            client.close()
                            continue
                        elif(request_fields[0] == 'GET'):
                            sendback = file_reader.get(path_to_pass, cookies)
                            size = file_reader.head(path_to_pass, cookies)
                            if(sendback == None):
                                print('[ERRO] [' + str(address[0]) + ':' + str(port_Number) + '] ' + request_fields[0] + ' returned error ' + '404')
                                message = 'HTTP/1.1 404 Not Found\r\n\r\n'.encode('utf-8')
                                client.send(message)
                                inputs.remove(client)
                                client.close()
                                continue
                            # message = "HTTP/1.1 200 OK\r\nContent-Length: " + str(size) + "\r\nContent-Type: " + content_type + \
                            #           "\r\n\r\n" +  sendback + "\r\n"
                            message = "HTTP/1.1 200 OK\r\nServer: rah9eu\r\nContent-Length: " + str(size) + "\r\nContent-Type: " + content_type + "\r\n\r\n"
                            message2 = "\r\n"
                            #print(size)
                            client.send(message.encode('utf-8'))
                            #print("message 1 sent")
                            try:
                                client.send(sendback.encode('utf-8'))
                            except:
                                client.send(sendback)
                            #print("payload sent")
                            #client.send(message2.encode('utf-8'))
                            #print("processed")

                            inputs.remove(client)
                            client.close()
                            continue
                            

if __name__ == "__main__":
    #port = int(sys.argv[1])
    #file_path = sys.argv[2]
    port = 6969
    file_path = r'C:\Users\Student\Documents\CS 4457\Project 2'
    FR = FileReader()

    J = Jewel(port, file_path, FR)
