from .Protocol import *
from .Structure import *
from .Log_Manager import Log
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import secrets
import pickle
import base64
import json
import uuid
import re


class Handler:
    def __init__(self) -> None:
        self.http=HyperTextTransferProtocol()
        self.Thread=self.http.Thread
        self.ServerUsersDB=set([])
        self.Sessions = set([])
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
        Request=thread.result
        first_line = thread.result[0]
        if 'GET' in first_line:
            Response=self.HandleGETRequest(Request)
        elif 'POST' in first_line[0]:
            Response=self.HandlePOSTRequest(Request)
        else:
            raise Exception('This communication is not HTTP protocol')
        self.http.SendResponse(Response, socket_and_address)
        self.Thread.find_stopped_thread()
        self.Thread.ThreadDestructor(thread_name, client_address)

    def HandleGETRequest(self, Request):
        result = parse.unquote(Request[0]).split(' ')[1].replace('\\','/')
        try:
            Response = self.HandleTextFileRequest()
            if '?print=' in result:
                Response = self.HandleTextFileRequest(msg=result.split('=')[1])
            elif '.png' in result:
                Response= self.HandleFileRequest(f'{result}')
            elif '.ico' in result:
                Response=self.HandleFileRequest(result)
            elif '/upload_form' == result:
                Response= self.HandleTextFileRequest('/upload_form.html')
            elif not self.verifySessionCookie(Request)[0]:
                if '/SignUp_form' == result:
                    Response= self.HandleTextFileRequest('/SignUp_form.html')
                elif '/Login_form' == result:
                    Response= self.HandleTextFileRequest('/Login_form.html')
            elif (self.verifySessionCookie(Request)[0] and '/Logout_form' == result):
                Response= self.HandleTextFileRequest('/Logout_form.html')
            elif '.html' in result:
                Response=self.HandleTextFileRequest(result)
            return Response
        except FileNotFoundError:
            with open('resource/Error_Form.html','r',encoding='UTF-8') as arg:
                print(f'해당 resource{result}파일을 찾을수 없습니다.')
                Error_Response=arg.read().format(msg=f'해당 resource{result}파일을 찾을수 없습니다.').encode('utf-8')
                return PrepareHeader()._response_headers('404 Not Found',Error_Response) + Error_Response

    def HandlePOSTRequest(self,Request):
        JsonData=parse.unquote(Request[1])
        DictPostData=json.loads(JsonData)
        Form=DictPostData['Form']
        Response=self.HandleTextFileRequest()
        is_valid_cookie,cookie_value=self.verifySessionCookie(Request[0])
        try:
            if Form == 'SignUp':
                Response=self.SignUp_Handler(DictPostData['UserID'],DictPostData['UserName'],DictPostData['UserPw'],is_valid_cookie)
            elif Form == 'Login':
                Response=self.Login_Handler(DictPostData['UserID'],DictPostData['UserPw'],is_valid_cookie)
            elif Form == 'Logout':
                Response=self.Logout_Handler(cookie_value)
        except Exception as e:
            Response=self.ErrorHandler('400 Bad Request',e)
        return Response

    def verifySessionCookie(self,RequestData:list):
        for data in RequestData:
            if ('Cookie' in data and 'SessionID=' in data):
                Values = data.split('SessionID=')[1]
                for Session in self.Sessions:
                    if Values==Session.SessionToken:
                        return True, Values
        return False, None

    def HandleFileRequest(self,img_file='/a.png'):
        with open(f'resource{img_file}', 'rb') as ImgFile:
            Response_file=ImgFile.read()
            return PrepareHeader()._response_headers('200 OK',Response_file) + Response_file
        
    def HandleTextFileRequest(self,flie='/Index.html',Cookie=None):
        with open(f'resource{flie}','r',encoding='UTF-8') as TextFile:
            Response_file=TextFile.read().encode('UTF-8')
        return PrepareHeader()._response_headers('200 OK',Response_file,Cookie) + Response_file
    
    def ErrorHandler(self,Error_code,Error_msg):
        with open(f'resource/Error_Form.html','r',encoding='UTF-8') as TextFile:
            Response_file=TextFile.read()
            Response_file=Response_file.replace('{0}',Error_code).replace('{1}',Error_msg).encode('utf-8')

        return PrepareHeader()._response_headers('200',Response_file) + Response_file
    
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

    def SignUp_Handler(self,UserID,UserName,UserPw,is_valid_cookie):
        UserUID=uuid.uuid5(uuid.UUID('30076a53-4522-5b28-af4c-b30c260a456d'), UserID)
        if self.Sessions and is_valid_cookie:
            return self.ErrorHandler('403 Forbidden','Warning: You are already logged in. There is no need to log in again. You can continue using the current account.')
        for DB in self.ServerUsersDB:
            if (UserUID == DB.UserUID):
                return self.ErrorHandler('406 Not Acceptable',f'User information error! Duplicate ID! : {UserID}')  
        try:
            AuthenticatedName,AuthenticatedPassword=Verify().VerifyCredentials(UserName, UserPw)
        except Exception as e:
            return self.ErrorHandler('403 Forbidden',f'{e} : {UserName,UserPw}')
        DB=StructDB(UserUID,AuthenticatedName,AuthenticatedPassword)
        self.ServerUsersDB.add(DB)
        self.log(f"[ New DataBase Constructed ] ==> DBID : \033[95m{DB.DataBaseID}\033[0m")
        self.log(f"[ SignUp User ] ==> UUID : \033[96m{UserUID}\033[0m")
        self.HandleSaveDB()
        return self.HandleTextFileRequest('/SignUp_Action.html')

    def Login_Handler(self, user_id, user_pw ,is_valid_cookie):
        user_uid = uuid.uuid5(uuid.UUID('30076a53-4522-5b28-af4c-b30c260a456d'), user_id)
        # Check if user is already logged in
        if self.Sessions and is_valid_cookie:
            return self.ErrorHandler('403 Forbidden','Warning: You are already logged in. There is no need to log in again. You can continue using the current account.')
        # Check user credentials and create new session
        for db in self.ServerUsersDB:
            if user_uid == db.UserUID and user_pw == db.UserPw:
                session_id = self.RegisterUserSession(7, {'UserUID': user_uid})
                self.log(f"[ New Session Constructed ] ==> SessionID: \033[96m{session_id}\033[0m")
                return self.HandleTextFileRequest('/Login_Action.html',Cookie=f'SessionID = {session_id}')       
        return self.ErrorHandler('422 Unprocessable Entity',f'User ID or password does not exist: {user_id, user_pw}')

    
    def Logout_Handler(self,SessionID):
        for Session in self.Sessions:
            if Session.SessionToken == SessionID:
                self.Sessions.remove(Session)
                self.log(f"[ Session Destructed ] ==> SessionID : \033[96m{SessionID}\033[0m")
                return self.HandleTextFileRequest('/Logout_Action.html')
        return self.ErrorHandler('403 Forbidden',f'To log out, you must first log in. Please verify your account information and log in before attempting to log out')

    def RegisterUserSession(self,  SessionValidityDays: str, UserInfo: dict):
        SessionInfo = Session(SessionValidityDays, UserInfo)
        self.Sessions.add(SessionInfo)
        return SessionInfo.SessionToken

    def HandleSaveDB(self):
        with open(f'resource/ServerUserDB.DB','wb') as DBfile:
            pickle.dump(self.ServerUsersDB,DBfile)
            self.log(f"[ Database Save Successful ] ==> path : \033[95mresource/ServerUserDB.DB\033[0m")

    def HandleloadDB(self):
        try:
            with open(f'resource/ServerUserDB.DB','rb') as DBfile:
                self.ServerUsersDB=pickle.load(DBfile)
                self.log(f"[ Database Load Successful ] ==> path : \033[95mresource/ServerUserDB.DB\033[0m")
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

    def __hash__(self):
        return hash(self.SessionToken)

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

