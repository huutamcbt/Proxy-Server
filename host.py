class Client():
    def __init__(self):
        self.clientSocket = ""
        self.clientAddress = ""
    
    
    def getAllowedHosts(self):
        file = open("files/configuration_files/allowedhosts.conf", "r")
        data = file.read()
        file.close()
        # get the allowed hosts 
        host_list = data.split("\n")

        return  host_list


    def isHostAllowed(self):
        # extract host from client Address
        host = self.clientAddress[0]

        # check whether host is on the allowed host list or not
        for allowed_host in self.getAllowedHosts():
            if(host in allowed_host):
                return True

        return False


    def printList(self):
        for i, j in zip(range(len(self.getAllowedHosts())-1), self.getAllowedHosts()):
            print(str(i) + ". " + str(j))


    def findHost(self, host):
        index = 0
        for i in self.getAllowedHosts():
            if(host == i):
                return index
            index += 1
        
        return -1


    def addHost(self, host):
        if(self.findHost(host) == -1):
            file = open("files/configuration_files/allowedhosts.conf", "a")
            file.write(host)
            file.write("\n")
            file.close()
      
        print("You added the new host successfully")


    def removeHost(self, host):
        i = 0
        index = self.findHost(host)
        if(index != -1):
            file = open("files/configuration_files/allowedhosts.conf", "r")
            data = file.readlines()
            file.close()
            new_file = open("files/configuration_files/allowedhosts.conf", "w")
            for line in data:
                if(index == i):
                    new_file.write(" ")
                else:
                    new_file.write(line)
                    i += 1
            new_file.close()
        
        print("You removed the host successfully")