import socket    #for sockets
import sys    #for exit

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print('Failed to create socket')
    sys.exit()

#host = '192.168.2.164';
host = 'minibot';
port = 4210;

while(1) :
    try:
        msg = input('Enter command : ')
        frame = msg.split()
        # turn angle in deg
        if("turn" in frame[0]):
            msg = "1 "+str(round(float(frame[1])*22.575))+" "+str(round(float(frame[1])*(-22.575)))
            print(msg)
        # move distance in cm
        if("move" in frame[0]):
            msg = "1 "+str(round(float(frame[1])*21.558*10))+" "+str(round(float(frame[1])*(21.558*10)))
            print(msg)
        try :
            #Set the whole string
            s.sendto(msg.encode(), (host, port))
            s.settimeout(1)
            
            # receive data from client (data, addr)
            d = s.recvfrom(1024)
            reply = d[0]
            addr = d[1]
            
            print('Server reply : ' + reply.decode())
        except socket.timeout:
            print("Timeout")
        except socket.error:
            print('Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            sys.exit()
    except KeyboardInterrupt:
        print("closing socket")
        s.close()
        sys.exit()