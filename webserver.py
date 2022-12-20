class WebServer:
    def __init__(self):
        self.webServer = ""
        self.port = -1

    
    def getBlacklist(self):
        # open blacklist.conf file
        file = open("files/configuration_files/blacklist.conf", "r")
        data = file.read()
        file.close()
        # get list of domain name in blacklist
        domain_list = data.split("\n")

        return domain_list


    def isServerDenied(self):
        # check whether server is on blacklist or not
        for domain in self.getBlacklist():
            if (self.webServer in domain):
                return True  

        return False


    def printList(self):
        for i, j in zip(range(len(self.getBlacklist())-1), self.getBlacklist()):
            print(str(i) + ". " + str(j))


    def findDomainName(self, domain):
        index = 0
        for i in self.getBlacklist():
            if(domain == i):
                return index
            index += 1
        
        return -1


    def addDomainName(self, domain):
        if(self.findDomainName(domain) == -1):
            file = open("files/configuration_files/blacklist.conf", "a")
            file.write(domain)
            file.write("\n")
            file.close()
      
        print("You added the new domain name successfully")


    def removeDomainName(self, domain):
        i = 0
        index = self.findDomainName(domain)
        if(index != -1):
            file = open("files/configuration_files/blacklist.conf", "r")
            data = file.readlines()
            file.close()
            new_file = open("files/configuration_files/blacklist.conf", "w")
            for line in data:
                if(index == i):
                    new_file.write(" ")
                else:
                    new_file.write(line)
                    i += 1
            new_file.close()
        
        print("You removed the domain name successfully")