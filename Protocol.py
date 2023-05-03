import socket
from urllib import request
from urllib import parse
from Thread_Manager import *
from Structure import *
from Log_Manager import *

class HyperTextTransferProtocol:
    def __init__(self):
        self.head = bytes()
        self.recv_datas = bytes()
        self.s = socket.socket()
        self.Thread=Thread()
        self.log=Log().logging
        self.Content_Length=''
        self.DB=DBManager()

    def start_web_server(self):
        self.bind_address()
        self.listen()
        while True:
            user_info=self.accept_connection()
            self.Thread.Create_Thread(target=self.handle_request_thread,args=user_info)[1].start()
    
    def handle_request_thread(self, client_socket, client_address):
        socket_and_address = [(client_socket,), client_address]
        thread_name, thread = self.assign_user_thread(socket_and_address)
        thread.start()
        thread.join()
        first_line = thread.result[0]
        if 'GET' in first_line:
            query=self.HandleGETRequest(thread)
        elif 'POST' in first_line:
            file_name=thread.result[1][1].split('"')[3]
            self.ImgFileUpload(thread.result[2],f'{file_name}')
            query=self.HandleImgFileRequest(self.DB.ServerDB['Img'][file_name])
        else:
            return 'This communication is not HTTP protocol'
        self.send_response(query, socket_and_address)
        self.Thread.find_stopped_thread()
        self.Thread.clearSessionInfo(thread_name, client_address)

    def bind_address(self, address='0.0.0.0', port=80):
        external_ip = request.urlopen('https://ident.me').read().decode('utf8')  
        self.s.bind((address, port))
        self.log(f"[Server started on] ==> \033[96m{external_ip}:{port}\033[0m")

    def listen(self, limit=0):
        self.s.listen(limit)

    def accept_connection(self):
        self.c, self.addr = self.s.accept()
        self.log(msg=f"[Connected with] ==> \033[32m{self.addr}\033[0m")
        return self.c, self.addr
    
    def receive(self,socket=None, addres=None, max_recv_size=1):
        received_data = b''
        header_list=list()
        while b'\r\n\r\n' not in received_data:
            if socket is None:
                received_data += self.c.recv(max_recv_size)
            received_data += socket[0].recv(max_recv_size)
            header_list=received_data.decode().split('\r\n')
        if 'POST' in header_list[0]:
            post_header=self.receive(socket,addres)[1]
            post_body=b''
            for count in range(int(self.ExtractPostBodySize(header_list)/2048)):
                post_body+=socket[0].recv(2048)
            return 'POST',post_header,post_body
        self.log(msg=f'[{parse.unquote(header_list[0])} request from] ==> \033[33m{addres}\033[0m')
        return 'GET',header_list

    def assign_user_thread(self,socket_and_addres):
        thread_name,thread = self.Thread.Create_Thread(target=self.receive,args=socket_and_addres)
        self.Thread.USERS.append(socket_and_addres[1])
        self.Thread.USERS_COUNT+=1
        self.Thread.SESSIONS[thread_name]=socket_and_addres[1]
        self.Thread.user_socket_dict[socket_and_addres[1]]=socket_and_addres[0]
        return thread_name,thread

    def send_response(self,query,socket_and_addres):
        addr = f'\033[31m{socket_and_addres[1]}\033[0m'
        socket_and_addres[0][0].send(query)
        socket_and_addres[0][0].close()
        self.log(msg=f'[Disconnected from] ==> {addr}')
        self.Thread.finished_users.append(socket_and_addres[1])

    def HandleGETRequest(self, thread):
        result = parse.unquote(thread.result[1][0]).split(' ')[1].replace('\\','/')
        try:
            Response = self.HandleTextFileRequest()
            if '?print=' in result:
                Response = self.HandleTextFileRequest(query=result.split('=')[1])
            elif '.ico' in result:
                Response=self.HandleImgFileRequest(result)
            elif '.html' in result:
                Response=self.HandleTextFileRequest(result)
            elif '.png' in result:
                Response= self.HandleImgFileRequest(f'{result}')
            elif '/upload_from' == result:
                Response= self.HandleTextFileRequest('/upload_from.html')
            return Response
        except FileNotFoundError:
            with open('resource/nofile.html','r') as arg:
                print(f'해당 resource{result}파일을 찾을수 없습니다.')
                Error_Response=arg.read().format(msg=f'해당 resource{result}파일을 찾을수 없습니다.').encode('utf-8')
                return PrepareHeader()._response_headers(Error_Response) + Error_Response

    def ExtractPostBodySize(self, header):
        content_length_header = next((header for header in header if 'Content-Length' in header), None)
        if content_length_header:
            content_length_str = ''.join(filter(str.isdigit, content_length_header))
            return int(content_length_str)
        return 0
        
    def HandleImgFileRequest(self,img_file='/a.png'):
        with open(f'resource{img_file}', 'rb') as ImgFile:
            Response_file=ImgFile.read()
            return PrepareHeader()._response_headers(Response_file) + Response_file
        
    def HandleTextFileRequest(self,flie='/Hello world.html', query='아무튼 웹 서버임'):
        with open(f'resource{flie}','r') as TextFile:
            Response_file=TextFile.read().format(msg=query)
        return PrepareHeader()._response_headers(Response_file) + Response_file.encode('utf-8')
    
    def ImgFileUpload(self,img_file,file_name):
        self.DB.loadDB()
        with open(f'resource/ImgFileUpload{file_name}', 'wb') as ImgFile:
            ImgFile.write(img_file)
            self.DB.ServerDB['Img']={file_name:f'/ImgFileUpload/{file_name}'}
            print(self.DB.ServerDB)
            self.DB.SaveDB()
            return file_name
        
        
HyperTextTransferProtocol().start_web_server()