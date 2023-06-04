from .Protocol import *
from .Structure import StructDB
from .Log_Manager import Log
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import secrets
import base64
import uuid
import re


class Handler:
    def __init__(self) -> None:
        self.http=HyperTextTransferProtocol()
        self.Thread=self.http.Thread
        self.ServerUsersDB=[]
        self.Sessions = []
        self.ServerDB={}
        self.log=Log().logging
        self.HandleloadDB()

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
            post_data=parse.unquote(thread.result[1])
            if '&' in post_data:
                UserInfo=post_data.split('&')
                if len(UserInfo) == 3:
                    query=self.Sign_Up_handler(UserInfo[0],UserInfo[1],UserInfo[2])
                elif len(UserInfo) == 2:
                    query=self.login_handler(UserInfo[0],UserInfo[1])

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
            elif not self.verifySessionCookie(thread.result[1])[0]:
                if '/signup_form' == result:
                    Response= self.HandleTextFileRequest('/signup_form.html')
                elif '/login_form' == result:
                    Response= self.HandleTextFileRequest('/login_form.html')
            elif (self.verifySessionCookie(thread.result[1])[0] and '/logout_form' == result):
                Response= self.HandleTextFileRequest('/logout_form.html')
            return Response
        except FileNotFoundError:
            with open('resource/Hello world.html','r',encoding='UTF-8') as arg:
                print(f'해당 resource{result}파일을 찾을수 없습니다.')
                Error_Response=arg.read().format(msg=f'해당 resource{result}파일을 찾을수 없습니다.').encode('utf-8')
                return PrepareHeader()._response_headers('404 Not Found',Error_Response) + Error_Response
            
    def verifySessionCookie(self,RequestData:list):
        for data in RequestData:
            if ('Cookie' in data):
                for Values in data.split('SessionID='):
                    for Session in self.Sessions:
                        if Values==Session.SessionToken:
                            return True, Values
        return False, None

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


    def Sign_Up_handler(self,UserID,UserName,UserPw):
        UserUID=uuid.uuid5(uuid.UUID('30076a53-4522-5b28-af4c-b30c260a456d'), UserID)
        for DB in self.ServerUsersDB:
            if (UserUID == DB.UserUID):
                return self.HandleTextFileRequest(query=f'User information error! Duplicate ID! : {UserID}')
        try:
            AuthenticatedName,AuthenticatedPassword=Verify().VerifyCredentials(UserName.split('=')[1], UserPw.split('=')[1])
        except Exception as e:
            return self.HandleTextFileRequest(query=f'User information error! Invalid nickname or password : {UserName,UserPw}')
        self.ServerUsersDB.append(StructDB(UserUID,AuthenticatedName,AuthenticatedPassword))
        self.log(f"[ SignUp User ] ==> UUID : \033[96m{UserUID}\033[0m")
        self.HandleSaveDB()
        return self.HandleTextFileRequest(query=f'Thanks for signing up!\n\nWelcome!')

    def login_handler(self,UserID,UserPw):
        UserPw=UserPw.split('=')[1]
        UserUID=uuid.uuid5(uuid.UUID('30076a53-4522-5b28-af4c-b30c260a456d'), UserID)
        for DB in self.ServerUsersDB:
            if (UserUID == DB.UserUID and UserPw == DB.UserPw):
                SessionID=self.RegisterUserSession(7,UserInfo={'UserUID':UserUID})
                self.log(f"[ New Session Created ] ==> SessionID : \033[96m{SessionID}\033[0m")
                with open(f'resource/Hello world.html','r',encoding='UTF-8') as TextFile:
                    Text=TextFile.read()
                    Response_file=Text.format(msg=f"Login complete!\n\nWelcome! User : {UserUID}").encode('UTF-8')
                    return PrepareHeader()._response_headers('200 OK',Response_file,Cookie=f'SessionID = {SessionID}') + Response_file
        return self.HandleTextFileRequest(query=f'User ID or password does not exist : {UserID,UserPw}')

    def RegisterUserSession(self,  SessionValidityDays: str, UserInfo: dict):
        SessionInfo = Session(SessionValidityDays, UserInfo)
        self.Sessions.append(SessionInfo)
        return SessionInfo.SessionToken

    def HandleSaveDB(self):
        with open(f'resource/ServerUserDB.DB','wb') as DBfile:
            pickle.dump(self.ServerUsersDB,DBfile)
            self.log(f"[ Database Save Successful ] ==> \033[96mresource/ServerUserDB.DB\033[0m")

    def HandleloadDB(self):
        try:
            with open(f'resource/ServerUserDB.DB','rb') as DBfile:
                self.ServerUsersDB=pickle.load(DBfile)
                self.log(f"[ Database Load Successful ] ==> \033[96mresource/ServerUserDB.DB\033[0m")
        except FileNotFoundError:
            pass

@dataclass
class Session:
    """
    Session class represents a data model for storing session information.

    Attributes:
        SessionToken (str): The token of the session. It is initialized as a 16-character random value.
        SessionValidity (float): The validity timestamp of the session.
        SessionValidityDays (int): The number of days the session is valid for.
        UserInfo (dict): Additional information about the session's user.
        SessionDict (dict): The dictionary representation of the session information.

    Methods:
        __post_init__(): Initializes the SessionToken, SessionValidity, and SessionDict attributes after object creation.
    """
    SessionToken: str = field(init=False, default=None)
    SessionValidity: float = field(init=False, default=None)
    SessionValidityDays: int
    UserInfo: dict = field(default_factory=dict)
    SessionDict: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """
        Initializes the SessionToken, SessionValidity, and SessionDict attributes after object creation.
        """
        self.SessionToken = SessionID(16).Token
        self.SessionValidity = (datetime.now() + timedelta(days=self.SessionValidityDays)).timestamp()
        self.SessionDict['SessionID'] = self.SessionToken
        self.SessionDict['SessionValidity'] = self.SessionValidity
        self.SessionDict['UserInfo'] = self.UserInfo

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

class Verify:

    def __init__(self) -> None:
        pass

    def VerifyCredentials(self, UserID, UserPw):
        if not self._VerifyUserID(UserID):
            raise Exception("Name cannot contain spaces or special characters")
        elif not self._VerifyUserPw(UserPw):
            raise Exception("Your password is too short or too easy. Password must be at least 8 characters and contain numbers, English characters and symbols. Also cannot contain whitespace characters.")
        else:
            return UserID, UserPw

    def _VerifyUserID(self, UserID):
        if (" " not in UserID and "\r" not in UserID and "\n" not in UserID and "\t" not in UserID and re.search('[`~!@#$%^&*(),<.>/?]+', UserID) is None):
            return True
        return False

    def _VerifyUserPw(self, UserPw):
        if (len(UserPw) > 8 and re.search('[0-9]+', UserPw) is not None and re.search('[a-zA-Z]+', UserPw) is not None and re.search('[`~!@#$%^&*(),<.>/?]+', UserPw) is not None and " " not in UserPw):
            return True
        return False

    def _NameDuplicateCheck(self):
        if len(self.ServerDB) != 0:
            for item in self.ServerDB.items():
                return item['user_ID']==self.verified_UserID
        else: return False

