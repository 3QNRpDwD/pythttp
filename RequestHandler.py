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
    """
    Sessions is a data class that holds the session information for the system.
    """
    UserID: str
    SessionValidityDays: int
    SessionToken: str = field(init=False, default=None)
    SessionInfo: Dict[str, Set[Tuple[str, float]]] = field(init=False, default_factory=dict)

    def __post_init__(self):
        """
        Method called after object initialization.
        Adds or updates session information.

        Explanation:
        This method is called automatically after the object is initialized.
        It is responsible for adding or updating session information in the SessionInfo dictionary.
        It generates a unique token using the SessionID class, with a length of 16 characters.
        Then, it calculates the session validity by adding the SessionValidityDays to the current datetime
        and converting it to a timestamp.

        If the generated token already exists in the SessionInfo dictionary, it adds a tuple with the
        UserID and session validity to the existing set of session information.
        Otherwise, it creates a new key-value pair in the SessionInfo dictionary, with the token as the key
        and a set containing a tuple of the UserID and session validity as the value.
        """
        self.SessionToken = SessionID(16).Token
        session_validity = (datetime.now() + timedelta(days=self.SessionValidityDays)).timestamp()

        if self.SessionToken in self.SessionInfo:
            self.SessionInfo[self.SessionToken].add((self.UserID, session_validity))
        else:
            self.SessionInfo[self.SessionToken] = {(self.UserID, session_validity)}
    
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
        self.Sessions = {}

    def RegisterUserSession(self, UserID: str, SessionValidityDays: int):
        """
        Registers a user session and returns the session token.

        Parameters:
        - UserID (str): The ID of the user.
        - SessionValidityDays (int): The number of days the session will be valid.

        Returns:
        - str: The session token generated for the user.

        Explanation:
        This method is used to register a user session by creating a new session for the given user ID
        and session validity. It generates a session token and calculates the session's validity period.

        First, a new Session object called SessionInfo is created by passing the UserID and SessionValidityDays
        as arguments. This Session object is responsible for generating the session token and calculating
        the session validity.

        Next, the session information from SessionInfo is merged into the Sessions dictionary by calling
        the update() method. This adds or updates the session information for the user in the Sessions dictionary.

        Finally, the session token (SessionInfo.SessionToken) is returned, which represents the generated
        session token for the user.

        """
        SessionInfo = Session(UserID, SessionValidityDays)
        self.Sessions.update(SessionInfo.SessionInfo)
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