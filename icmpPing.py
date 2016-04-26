import socket
import sys
import os
import struct
import select
import time

from sys import argv



ICMP_ECHO_REQUEST = 8 


#Calculate the Checksum

def checksum(source):
   
    sum = 0
    length = (len(source)/2)*2
    counter = 0
    while counter<length:
        value = ord(source[counter + 1])*256 + ord(source[counter])
        sum = sum + value
        sum = sum & 0xffffffff 
        counter = counter + 2
    if length<len(source):
        sum = sum + ord(source[len(source) - 1])
        sum = sum & 0xffffffff 

    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)

    result = ~sum
    result = result & 0xffff

    result = result >> 8 | (result << 8 & 0xff00)
    return result

#Receive the ping

def receive(my_socket, ID, timeout):


    timeLeft = timeout
    while 1>0:
        startedSelect = time.clock()
        whatReady = select.select([my_socket], [], [], timeLeft)

        howLongInSelect = (time.clock() - startedSelect)


        if whatReady[0] == []: 


            return

        timeReceived = time.clock()


        recPacket, addr = my_socket.recvfrom(1024)
        icmpHeader = recPacket[20:28]


        type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:


            return

#Send the Ping

def send(my_socket, dest_addr, ID):

    
    my_checksum = 0

    
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)


    bytesInDouble = struct.calcsize("d")


    data = (192 - bytesInDouble) * "Q"


    data = struct.pack("d", time.clock()) + data

    my_checksum = checksum(header + data)



    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1)
    packet = header + data
    my_socket.sendto(packet, (dest_addr, 1)) 



#Generate individual Ping 

def single_ping(address, timeout):
    
    icmp = socket.getprotobyname("icmp")


    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)


    except socket.error, (errno, msg):

        raise # raise the original error

    userId = os.getpid() & 0xFFFF

    send(sock, address, userId)
    responseTime = receive(sock, userId, timeout)



    sock.close()
    return responseTime


#Ping a given destination address

def ping(address, timeout = 3, numOfAttempts = 20):

    totalTime = 0
    success = 0.0
    packetsLost = 0.0
    minTime = 999999999
    maxTime = 0
    
    for x in xrange(numOfAttempts):

        print "ping %s..." % address,
        try:
            responseTime  =  single_ping(address, timeout)

        except socket.gaierror, e:
            print "failed. (socket error: '%s')" % e[1]
            break

        if responseTime  ==  None:
            print "failed. (timed out in %ssec.)" % timeout
            packetsLost = packetsLost + 1

        else:
            responseTime  =  responseTime * 1000
            print "ping received in %0.4fms" % responseTime
            success = success + 1
            totalTime = totalTime + responseTime
            #check min
            if responseTime<minTime:
                minTime = responseTime

            #check max
            if responseTime>maxTime:
                maxTime = responseTime

    print 
    print
    if packetsLost>0:
        lossRate = (packetsLost/ numOfAttempts) * 100
    else:
        lossRate = 0.0
        
    averageTime = totalTime / success
    print "STATISTICS:"
    print "Packet Loss Rate: %0.2f percent" % lossRate
    print "Average Response Time: %0.4fms" % averageTime
    print "Minimum Response Time: %0.4fms" % minTime
    print "Maximum Response Time: %0.4fms" % maxTime

#Main-Takes 1 command line argument (destination)

if __name__ == '__main__':

    script, address = argv
    
    address  =  socket.gethostbyname(address)
    print "Starting Ping..."
    print
    time.sleep(1)
    ping(address)
    
    

