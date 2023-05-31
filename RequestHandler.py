from .Protocol import *

class Handler:
    def __init__(self) -> None:
        self.http=HyperTextTransferProtocol()
        self.Thread=self.http.Thread
        self.ServerDB={}

    def RunServer(self):
        self.http.BindAddress()
        self.http.listen()
        while True:
            user_info=self.http.AcceptConnection()
            self.Thread.ThreadConstructor(target=self.HandleRequestThread,args=user_info)[1].start()
    
    def HandleRequestThread(self, client_socket, client_address):
        socket_and_address = [(client_socket,), client_address]
        thread_name, thread = self.http.AssignUserThread(socket_and_address)
        thread.start()
        thread.join()
        first_line = thread.result[0]
        if 'GET' in first_line:
            query=self.HandleGETRequest(thread)
        elif 'POST' in first_line:
            file_name=thread.result[1][1].split('"')[3]
            self.ImgFileUpload(thread.result[2],f'{file_name}')
            query=self.HandleFileRequest(self.ServerDB['Img'][file_name])
        else:
            return 'This communication is not HTTP protocol'
        self.http.SendResponse(query, socket_and_address)
        self.Thread.find_stopped_thread()
        self.Thread.SessionDestructor(thread_name, client_address)

    def HandleGETRequest(self, thread):
        result = parse.unquote(thread.result[1][0]).split(' ')[1].replace('\\','/')
        try:
            Response = self.HandleTextFileRequest()
            if '?print=' in result:
                Response = self.HandleTextFileRequest(query=result.split('=')[1])
            elif '.ico' in result:
                Response=self.HandleFileRequest(result)
            elif '.html' in result:
                Response=self.HandleTextFileRequest(result)
            elif '.png' in result:
                Response= self.HandleFileRequest(f'{result}')
            elif '/upload_from' == result:
                Response= self.HandleTextFileRequest('/upload_from.html')
            return Response
        except FileNotFoundError:
            with open('resource/Hello world.html','r',encoding='UTF-8') as arg:
                print(f'해당 resource{result}파일을 찾을수 없습니다.')
                Error_Response=arg.read().format(msg=f'해당 resource{result}파일을 찾을수 없습니다.').encode('utf-8')
                return PrepareHeader()._response_headers('404 Not Found',Error_Response) + Error_Response
        
    def HandleFileRequest(self,img_file='/a.png'):
        with open(f'resource{img_file}', 'rb') as ImgFile:
            Response_file=ImgFile.read()
            return PrepareHeader()._response_headers('200 OK',Response_file) + Response_file
        
    def HandleTextFileRequest(self,flie='/Hello world.html', query='아무튼 웹 서버임'):
        with open(f'resource{flie}','r',encoding='UTF-8') as TextFile:
            Text=TextFile.read()
            try:
                Response_file=self.addFormatToHTML(Text,self.ServerDB['Img'],'<img src="{val}" alt="{key}">\n\t').encode('UTF-8')
            except KeyError:
                Response_file=Text.format(msg=query,Format='').encode('UTF-8')
        return PrepareHeader()._response_headers('200 OK',Response_file) + Response_file
    
    def addFormatToHTML(self,HtmlText : str, FormatData : dict, style : str):
        Format=''
        for key,val in FormatData.items():
            Format+=f'{style.format(val=val,key=key)}'
        HtmlText=HtmlText.format(Format=Format)
        return HtmlText
    
    def ImgFileUpload(self,img_file,file_name):
        with open(f'resource/ImgFileUpload/{file_name}', 'wb') as ImgFile:
            ImgFile.write(img_file)
            self.ServerDB['Img']={file_name:f'/ImgFileUpload/{file_name}'}
            return file_name
        