import socket
import signal
import sys
import os
import time
import threading
import webserver
import host
import ssl

config = {
    "HOST_NAME": "127.0.0.1",
    "PORT": 5000,
    "BUFFER_SIZE": 5000,
    "MAX_REQUEST": 500,
    "RECEIVED_TIMEOUT": 1,
    "PERMISSION": True
}


class ProxyServer:
    def __init__(self, config):
        # Shutdown on  Ctrl + C
        signal.signal(signal.SIGINT, self.shutdown)

        # Create a TCP socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Reuse the socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to a public host and a port
        self.serverSocket.bind(('', config["PORT"]))

        self.serverSocket.listen(config["MAX_REQUEST"]) # become a server socket


    def runProxyServer(self):
        while config["PERMISSION"]:
            client = host.Client()
            
            # Establish the connection
            client.clientSocket, client.clientAddress = self.serverSocket.accept()
            
            # Create a thread for each request
            process = threading.Thread(target= self.redirectTraffic, name=client.clientAddress[0],args=(client,))
            process.daemon = True
            process.start()
            

    def redirectTraffic(self, client):
        # create a web server variable
        server = webserver.WebServer()
        
        # get the request from a browser
        request = client.clientSocket.recv(config["BUFFER_SIZE"])

        # extract the url from the request
        url = self.extractURL(request)

        # extract the domain name and port from the url
        server.webServer, server.port = self.getWebServerAddr(url)

        # check the validity of host nad domain name 
        if(server.isServerDenied() == True):
            print("A domain name {} is denied".format(server.webServer))
            if(server.port == 80):
                client.clientSocket.sendall(self.create403Response().encode())
            else:
                pass
            
        elif (client.isHostAllowed() == False):
            print("A host {} is not accepted".format(client.clientAddress))
            if(server.port == 80):
                client.clientSocket.sendall(self.create403Response().encode())
            else:
                pass
            
        else: # connect to server if the host and domain name are valid
            self.connectClientToServer(client, server, request)

        client.clientSocket.close()
     
        
    def extractURL(self, request):
        # decode the request
        data = request.decode("ISO-8859-1")

        # parse a first line of the request
        start_line = data.split("\n")[0]

        # get url
        url = start_line.split(" ")[1]
    
        return url


    def getWebServerAddr(self, url):
        http_pos = url.find("://") # find position of ://
        if(http_pos == -1):
            temp = url
        else: 
            temp = url[(http_pos + 3):] # get the rest of url  

        port_pos = temp.find(":") # find the port position (if any)

        # find end of web server 
        webServer_pos = temp.find("/")
        if (webServer_pos == -1):
            webServer_pos = len(temp)

        webServer = ""
        port = -1

        if(port_pos == -1):
            port = 80 # default port
            webServer = temp[:webServer_pos]
        else: # specific port
            port = int(temp[(port_pos + 1):(webServer_pos)])
            webServer = temp[:port_pos]
        
        return webServer, port


    def getMethod(self, request):
        # decode the request
        data = request.decode("ISO-8859-1")

        # get method
        method = data.split(" ")[0]

        return method


    def connectClientToServer(self, client, server, connectionRequest):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            sock.connect((server.webServer, server.port))

            method = self.getMethod(connectionRequest)
            
            # Use CONNECT method for HTTPS protocol
            if(method == "CONNECT"):
                self.processCONNECT(sock, client, server.webServer)

            if(method == "GET"):
                
                self.processGET(sock, client, connectionRequest, server.webServer)
             
        except Exception as error:
            #print(error)
            pass
        sock.close()


    def processCONNECT(self, sock, client, webServer):
        connectionResponse = self.create200Response()
        client.clientSocket.sendall(connectionResponse.encode())
       
        client.clientSocket.setblocking(0)
        sock.setblocking(0)
        request = " "
        response = " "
        i = 0
        while config["PERMISSION"]:
            
            try:
                request = client.clientSocket.recv(config["BUFFER_SIZE"])
                
                if(len(request) <= 0):
                    print("break 1")
                    break
                sock.sendall(request)
                
            except Exception as e:
                
                pass
            try:
                response = sock.recv(config["BUFFER_SIZE"])
                
                if(len(response) <= 0):
                    print("break 2")
                    break
                client.clientSocket.sendall(response)
                
                print("[CONNECT] Request is accepted: {} send to {}".format(client.clientAddress[0], webServer))
            except Exception as e:
                
                pass
             

    def processGET(self, sock, client, connectionRequest, webServer):
        sock.sendall(connectionRequest)
        client.clientSocket.settimeout(config["RECEIVED_TIMEOUT"])
        sock.settimeout(config["RECEIVED_TIMEOUT"])
    
        while config["PERMISSION"]:
            try:
                response = sock.recv(config["BUFFER_SIZE"])
                if(len(response) <= 0):
                    print("break")
                    break
                client.clientSocket.sendall(response)
                response = ""
                print("[GET] Request is accepted: {} send to {}".format(client.clientAddress[0], webServer))
            except:
                break


    def connectProxy(self):
        while config["PERMISSION"]:
            client = host.Client()
            server = webserver.WebServer()
            client.clientSocket, client.clientAddress = self.serverSocket.accept()
            server.webServer = input("Type your proxy server address: ")
            server.port = input("Type your proxy server port: ")
            process = threading.Thread(target= self.transferData, args= (client, server))
            process.daemon = True
            process.start()
        

    def transferData(self, client, server):
        request = client.clientSocket.recv(config["BUFFER_SIZE"])

        method = self.getMethod(request)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server.webServer, server.port)
        sock.sendall(request)
        if(method == "CONNECT"):
            self.transferCONNECTMethod(client, sock)
        if(method == "GET"):
            self.transferGETMethod(client, sock)
        while config["PERMISSION"]:
            pass

        sock.close()
        
    def transferCONNECTMethod(self, client, sock):
        client.clientSocket.sendall(self.create200Response())
        client.clientSocket.setblocking(0)
        sock.setblocking(0)
        
        while config["PERMISSION"]:
            try:
                request = client.clientSocket.recv(config["BUFFER_SIZE"])
                if(len(request) <= 0):
                    break

                sock.sendall(request)
                request = ""
            except:
                pass

            try:
                response = sock.recv(config["BUFFER_SIZE"])
                if(len(response) <= 0):
                    break

                client.clientSocket.sendall(response)
                print("Received data from server")
                response = ""
            except:
                pass

        client.clientSocket.close()
        


    def transferGETMethod(self,client, sock):
        sock.settimeout(config["RECEIVED_TIMEOUT"])
    
        while config["PERMISSION"]:
            response = sock.recv(config["BUFFER_SIZE"])
            if(len(response) <= 0):
                break

            client.clientSocket.sendall(response)
            print("Received data from server")
        
        client.clientSocket.close()


    def create200Response(self):
        response = "HTTP/1.1 200 Connection Established\n\n"

        return response


    def create403Response(self):
        response = "HTTP/1.1 403 Forbidden\n\n"
        file = open("files/html_files/403-forbidden.html", "r")
        data = file.read()
        file.close()
        response += data

        return response


    def createHTTPS403Response(self):
        pass


    def shutdown(self, signum, frame):
        """ Handle the exiting server. Clean all traces """
        print("WARNING", -1, 'Shutting down gracefully...')
        config["PERMISSION"] = False
        time.sleep(2)
        #main_thread = threading.current_thread() # Wait for all clients to exit
        
        # for t in threading.enumerate():
        #     if t is main_thread:
        #         continue
        #         self.log("FAIL", -1, 'joining ' + t.getName())
         
        self.serverSocket.close()
    

class ExtraFunction:
    
    # define the clear function to clean the screen
    @staticmethod
    def clear():
        # for Windows
        if(os.name == "nt"):
            os.system("cls")
        elif (os.name == "posix"):
            os.system("clear")
        else:
            pass


    @staticmethod
    def removeEmptyLines():
        file1 = open("./files/configuration_files/blacklist.conf", "r")
        file2 = open("./files/configuration_files/allowedhosts.conf", "r")
        data1 = file1.readlines()
        data2 = file2.readlines()
        file1.close()
        file2.close()
        new_file1 = open("./files/configuration_files/blacklist.conf", "w")
        new_file2 = open("./files/configuration_files/allowedhosts.conf", "w")
        for line in data1:
            if(line.strip().strip("\n") != ""):
                new_file1.write(line)
        new_file1.close()

        for line in data2:
            if(line.strip().strip("\n") != ""):
                new_file2.write(line)
        new_file2.close()


    @staticmethod
    def createDomainNameMenu():
        server = webserver.WebServer()
        serverChoice = ""
        while True:
            ExtraFunction.removeEmptyLines()
            print("0.Type 0 and press Enter to exit this menu")
            print("1.Type 1 and press Enter to print a list of domain name")
            print("2.Type 2 and press Enter to find a domain name")
            print("3.Type 3 and press Enter to add a new domain name")
            print("4.Type 4 and press Enter to remove a domain name")
            
            serverChoice = input("Enter your choice: ")
            
            if(serverChoice == "0"):
                break
            elif(serverChoice == "1"):
                server.printList()
            elif(serverChoice == "2"):
                domain = input("Your domain name: ")
                index = server.findDomainName(domain)
                if(domain == ""):
                    print("Your domain name doesn't exist")
                elif(index != -1):
                    print("Your domain name is in line " + str(index))
                else:
                    print("Your domain name doesn't exist")
            elif(serverChoice == "3"):
                domain = input("Your domain name: ")
                server.addDomainName(domain)
            elif(serverChoice == "4"):
                domain = input("Your domain name: ")
                server.removeDomainName(domain)
            else:
                pass
            input()
            ExtraFunction.clear()


    @staticmethod
    def createHostMenu():
        
        client = host.Client()
        hostChoice = ""
        while True:
            ExtraFunction.removeEmptyLines()
            print("0.Type 0 and press Enter to exit this menu")
            print("1.Type 1 and press Enter to print a list of host")
            print("2.Type 2 and press Enter to find a host")
            print("3.Type 3 and press Enter to add a new host")
            print("4.Type 4 and press Enter to remove a host")

            hostChoice = input("Enter your choice: ")
            
            if(hostChoice == "0"):
                break
            elif(hostChoice == "1"):
                client.printList()
            elif(hostChoice == "2"):
                addr = input("Your host: ")
                index = client.findHost(addr)
                if(addr == ""):
                    print("Your host doesn't exist")
                elif(index != -1):
                    print("Your host is in line " + str(index))
                else:
                    print("Your host doesn't exist")
            elif(hostChoice == "3"):
                addr = input("Your host: ")
                client.addHost(addr)
            elif(hostChoice == "4"):
                addr = input("Your host: ")
                client.removeHost(addr)
            else:
                pass
            input()
            ExtraFunction.clear()


if __name__ == "__main__":
    
    while True:

        print("[Note that] To stop the proxy server you can press Ctrl + C")
        print(" 0.Type 0 and press Enter to exit this program")
        print(" 1.Type 1 and press Enter to add or delete a domain name to blacklist")
        print(" 2.Type 2 and press Enter to add or delete a user to allowed user list")
        print(" 3.Type 3 and press Enter to run a Proxy Server")
        print(" 4.Type 4 and press Enter to connect to another proxy server")

        choice = input("Enter your choice: ")

        ExtraFunction.removeEmptyLines()
        ExtraFunction.clear()
        
        if (choice == "0"):     # exit the proxy server
            break
        elif (choice == "1"):   # add, delete and find a domain name to blacklist
            ExtraFunction.createDomainNameMenu()
        elif (choice == "2"):   # add, delete and find a user to the allowed user list
            ExtraFunction.createHostMenu()
        elif (choice == "3"):   # run the Proxy Server
            try:
                config["PERMISSION"] = True
                proxy = ProxyServer(config)
                proxy.runProxyServer()
            except:
                pass
        elif (choice == "4"):   # connect to another proxy server
            try:
                config["PERMISSION"] = True
                proxy = ProxyServer(config)
                proxy.connectProxy()
            except:
                pass
        else:                   # skip in other cases
            key = " "
            while len(key) != 0:
                print("\nYour number is invalid!")
                key = input("Press Enter to reenter your choice.\n")

        print("\nWait a minute")
        time.sleep(0.5)

        # clear screen
        ExtraFunction.clear()
        
