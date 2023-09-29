import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading
import os 

class NetCat:
    def __init__(self, args, buffer=None): 
        self.args = args 
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)

    def send(self):
        self.socket.connect((self.args.target,self.args.port))
        print(f"connected to {self.args.target} port {self.args.port}")
        if self.buffer:
            self.socket.send(self.buffer)
        while True:    
            try:
                while True: 
                    recv_len = 1
                    response = ''
                    while recv_len:
                        data = self.socket.recv(4096)
                        recv_len = len(data)
                        response += data.decode()
                        if recv_len < 4096:  #in case the response is bigger than 4096 the loop will continue receiving data                     
                            break
                    print(response)
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())

            except KeyboardInterrupt:  #CTRL-C 
                print('User terminated.')
                self.socket.close()
                sys.exit(0)
    
    def listen(self):
        self.socket.bind((self.args.target, self.args.port)) 
        self.socket.listen(10)
        while True:
            try:
                client_socket, _ = self.socket.accept()
                print(f"connection accepted {client_socket.getsockname()}")
                client_thread = threading.Thread(target=self.handle,args=(client_socket,))
                client_thread.start()
            except ConnectionResetError:
                self.socket.close()
                sys.exit(0)
            except ConnectionAbortedError:
                self.socket.close()
                sys.exit(0)

            

    def handle(self, client_socket):
        if self.args.execute:
            output = execute(self.args.execute) 
            client_socket.send(output.encode())
        
        elif self.args.command:
            while True:        
                client_socket.send(b'\n----------- <# BIRBANET #> -----------\n')
                cmd_buffer = b'' 
                while '\n' not in cmd_buffer.decode():
                    cmd_buffer += client_socket.recv(64) 
                    recv_len = len(cmd_buffer)
                    if recv_len == 0:
                        self.socket.close()
                        sys.exit(0)
                    if recv_len < 64: #same as send
                        response = execute(cmd_buffer.decode())
                        if response:
                            if type(response) == str :  #in case you dont input anything execute returns a string
                                response = response.encode()
                            client_socket.send(response)
                            cmd_buffer = b''  
                            break  
                        else:
                            break

        elif self.args.upload: 
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break
            with open(self.args.upload, 'wb') as f:    
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())
        
    
    def run(self):
        if self.args.listen:
            self.listen() 
        else:
            self.send()


def execute(cmd):
    output = ''
    cmd = cmd.strip()
    if cmd:  
        if cmd.startswith("cd "):    
            directory = cmd[3:]
            try:
                os.chdir(f'{directory.strip()}')
                output=f"Changed directory to: {os.getcwd()}"
            except FileNotFoundError:
                output=f"Directory not found: {directory}"
            except PermissionError:
                output=f"Permission denied: {directory}"
            output=output.encode()            
        else:            
            try:
                output = subprocess.run(shlex.split(cmd), capture_output=True,text=True,check=True)
                output=output.stdout
            except subprocess.CalledProcessError as e:
                print
                output='\n'+str(e.stdout)+str(e.stderr)
            output=output.encode()
                
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(   description='Net Tool', 
                                        formatter_class=argparse.RawDescriptionHelpFormatter,
                                        epilog=textwrap.dedent('''Example:\n
netcat.py -t 192.168.1.108 -p 5555 -l -c                         # command shell \n
netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt              # upload to file \n
netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\"       # execute command \n
echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135                 # echo text to server port 135 \n
netcat.py -t 192.168.1.108 -p 5555                               # connect to server\n
'''))
    
    parser.add_argument('-c', '--command',action='store_true', help='command shell')
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-l', '--listen',action='store_true', help='listen')
    parser.add_argument('-p', '--port', type=int,default=5555, help='specified port')
    parser.add_argument('-t', '--target',default='192.168.1.203', help='specified IP')
    parser.add_argument('-u', '--upload', help='upload file')
    
    args = parser.parse_args()

    if args.listen:
        buffer = ''
    else:
        print("CTRL-D")
        buffer = sys.stdin.read()
    
    nc = NetCat(args, buffer.encode())
    nc.run()