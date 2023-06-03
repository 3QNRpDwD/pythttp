from .Protocol import *
from .Structure import DBManager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Set, Tuple
import secrets
import base64
import uuid
import re


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
        if 'Header' == first_line:
            query=self.HandleGETRequest(thread)
        # elif 'Body' == first_line:
        #     query=self.HandleTextFileRequest()
            # file_name=thread.result[1][1].split('"')[3]
            # self.ImgFileUpload(thread.result[1][4].encode(),f'{file_name}')
            # query=self.HandleFileRequest(self.ServerDB['Img'][file_name])
        elif 'Body' == first_line:
            print(thread.result)
        else:
            return 'This communication is not HTTP protocol'
        self.http.SendResponse(query, socket_and_address)
        self.Thread.find_stopped_thread()
        self.Thread.ThreadDestructor(thread_name, client_address)

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
            elif '/upload_form' == result:
                Response= self.HandleTextFileRequest('/upload_form.html')
            elif '/login_form' == result:
                Response= self.HandleTextFileRequest('/login_form.html')
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

    def Sign_Up_handler(self):
            if self.SU._name_duplicate_check():
                '클라이언트로 에러 전송'
                return "This user already exists."
            

    def login_handler(self):
        pass


@dataclass
class Session:

    SessionToken: str = field(init=False, default=None)
    SessionValidity: float = field(init=False, default=None)
    SessionValidityDays: int
    UserInfo: dict = field(default_factory=dict)
    SessionDict: Set[Dict[str, str]] = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.SessionToken = SessionID(16).Token
        self.SessionValidity = (datetime.now() + timedelta(days=self.SessionValidityDays)).timestamp()
        self.SessionDict['SessionID']=self.SessionToken
        self.SessionDict['SessionValidity']=self.SessionValidity
        self.SessionDict['UserInfo']=self.UserInfo


@dataclass
class SessionID:
    """
    Data class representing a session identifier.

    python
    Copy code
    Attributes:
    length (int): The length of the session identifier.
    Token (str): The session token (automatically generated).

    """
    length: int
    Token: str = field(init=False, default=None)

    def __post_init__(self):
        """
        Method executed after initialization.
        Generates the session token.
        
        """
        self.Token = secrets.token_hex(self.length)

class SessionsManager:
    def __init__(self) -> None:
        self.Sessions = []

    def RegisterUserSession(self,  SessionValidityDays: str, UserInfo: dict):
        SessionInfo = Session(SessionValidityDays, UserInfo)
        self.Sessions.append(SessionInfo)
        return SessionInfo.SessionToken

class Verify:
    def __init__(self) -> None:
        pass

    def VerifyCredentials(self,UserID, UserPw):
        if not self._verify_userID(UserID):
            raise Exception("Name cannot contain spaces or special characters")
        elif not self._verify_userpw(UserPw):
            raise Exception("Your password is too short or too easy. Password must be at least 8 characters and contain numbers, English characters and symbols. Also cannot contain whitespace characters.")
        else:
            return UserID, UserPw

    def _VerifyUserID(self, UserID):
        if (" " not in self.UserID and "\r\n" not in self.UserID and "\n" not in self.UserID and "\t" not in self.UserID and re.search('[`~!@#$%^&*(),<.>/?]+', self.UserID) is None):
            return True
        return False

    def _VerifyUserPW(self, UserPw):
        if (len(self.Userpwrd) > 8 and re.search('[0-9]+', self.Userpwrd) is not None and re.search('[a-zA-Z]+', self.Userpwrd) is not None and re.search('[`~!@#$%^&*(),<.>/?]+', self.Userpwrd) is not None and " " not in self.Userpwrd):
            return True
        return False

    def _NameDuplicateCheck(self):
        if len(self.ServerDB) != 0:
            for item in self.ServerDB.items():
                return item['user_ID']==self.verified_UserID
        else: return False