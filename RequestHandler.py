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
import os


class Handler:
    def __init__(self) -> None:
        self.http=HyperTextTransferProtocol()
        self.Thread=self.http.Thread
        self.ServerUsersDB=set([])
        self.Sessions = set([])
        self.ServerPostDB=[]
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
            Response=self.ErrorHandler('405 Method Not Allowed',first_line)
        self.http.SendResponse(Response, socket_and_address)
        self.Thread.find_stopped_thread()
        self.Thread.ThreadDestructor(thread_name, client_address)

    def HandleGETRequest(self, Request):
        result = parse.unquote(Request[0]).split(' ')[1].replace('\\', '/')
        is_valid_cookie, cookie_value, session = self.verifySessionCookie(Request)
        print(result,is_valid_cookie)
        
        try:
            temporaryResponse = self.HandleTextFileRequest()
            
            if any(extension in result for extension in ['.png', '.html', '.css', '.js', '.ico']):
                temporaryResponse = self.HandleFileRequest(result)
            elif result == '/Feed_Page':
                temporaryResponse = self.UpdateFeedPage()
            elif not is_valid_cookie:
                if result in ['/SignUp_form', '/Login_form']:
                    temporaryResponse = self.HandleTextFileRequest(f'/html{result}.html')
            elif is_valid_cookie:
                if result == '/Logout_form':
                    temporaryResponse = self.HandleTextFileRequest(f'/html{result}.html')
                elif result == '/Account_Info':
                    temporaryResponse = self.HandleAccountFileRequest(Request)
            
            Response = PrepareHeader()._response_headers(temporaryResponse[0], temporaryResponse[1]) + temporaryResponse[1]
            
            if is_valid_cookie:
                cookie = {'SessionID': f'{cookie_value}; Expires={HttpDateTime().timestamp_to_http_datetime((datetime.now() + timedelta(days=1)).timestamp())}; Path=/'}
                Response = PrepareHeader()._response_headers(temporaryResponse[0], temporaryResponse[1], Cookie=cookie) + temporaryResponse[1]
            
            return Response
        except FileNotFoundError:
            with open('resource/html/Error_Form.html', 'r', encoding='UTF-8') as arg:
                return self.ErrorHandler('404 Not Found', f'The corresponding {result} file could not be found.')


    def HandlePOSTRequest(self, Request):
        JsonData = parse.unquote(Request[1].decode())
        DictPostData = json.loads(JsonData)
        Form = DictPostData['Form']
        Response = self.HandleTextFileRequest()
        is_valid_cookie, cookie_value, session = self.verifySessionCookie(Request[0])

        try:
            if Form == 'SignUp':
                temporaryResponse = self.SignUp_Handler(DictPostData['UserID'], DictPostData['UserEmail'], DictPostData['UserName'], DictPostData['UserPw'], is_valid_cookie)
            elif Form == 'Login':
                temporaryResponse = self.Login_Handler(DictPostData['UserID'], DictPostData['UserPw'], is_valid_cookie)
                if temporaryResponse[0] == '200 OK':
                    return PrepareHeader()._response_headers(temporaryResponse[0], temporaryResponse[1], Cookie=temporaryResponse[2]) + temporaryResponse[1]
            elif Form == 'Logout':
                temporaryResponse = self.Logout_Handler(is_valid_cookie,session)
                if temporaryResponse[0] == '200 OK':
                    return PrepareHeader()._response_headers(temporaryResponse[0], temporaryResponse[1], Cookie=temporaryResponse[2]) + temporaryResponse[1]
            elif Form == 'Account':
                temporaryResponse = self.UpdateAccount_Handler(DictPostData, session)
            elif Form == 'PostUpload':
                temporaryResponse = self.UploadPost_Handler(DictPostData, session)

            Response = PrepareHeader()._response_headers(temporaryResponse[0], temporaryResponse[1]) + temporaryResponse[1]

            if is_valid_cookie:
                cookie = {'SessionID': f'{cookie_value}; Expires={HttpDateTime().timestamp_to_http_datetime((datetime.now() + timedelta(days=1)).timestamp())}; Path=/'}
                Response = PrepareHeader()._response_headers(temporaryResponse[0], temporaryResponse[1], Cookie=cookie) + temporaryResponse[1]

            return Response
        
        except Exception as e:
            #Uncomment the following lines if you want to handle exceptions in a centralized manner
            Response = self.ErrorHandler('500 Internal Server Error', e)
            return Response


    def verifySessionCookie(self,RequestData:list):
        for data in RequestData:
            if ('Cookie' in data and 'SessionID=' in data):
                Values = data.split('SessionID=')[1]
                for Session in self.Sessions:
                    if Values==Session.SessionToken:
                        return True, Values ,Session
        return False, None, None
    
    def verifySessionExpires(self,Session):
        return False, None, None

    def HandleFileRequest(self,file='/img/a.png'):
        with open(f'resource{file}', 'rb') as ImgFile:
            Response_file=ImgFile.read()
            return '200 OK',Response_file
        
    def HandleTextFileRequest(self,flie='/html/Index.html'):
        with open(f'resource{flie}','r',encoding='UTF-8') as TextFile:
            Response_file=TextFile.read().encode('UTF-8')
        return '200 OK',Response_file
    
    def HandleLogoutRequest(self,session):
        with open(f'resource/html/Logout_Action.html','r',encoding='UTF-8') as TextFile:
            Response_file=TextFile.read().encode('UTF-8')
        cookie={'SessionID':f'{session.SessionToken}; Expires={HttpDateTime().timestamp_to_http_datetime((datetime.now() - timedelta(days=1)).timestamp())}; Path=/'}
        return '200 OK',Response_file,cookie
    
    def HandleLoginRequest(self,session):
        with open(f'resource/html/Login_Action.html','r',encoding='UTF-8') as TextFile:
            Response_file=TextFile.read().encode('UTF-8')
        cookie={'SessionID':f'{session.SessionToken}; Expires={session.SessionValidity}; Path=/'}
        return '200 OK',Response_file,cookie
    
    def ErrorHandler(self,Error_code,Error_msg):
        with open(f'resource/html/Error_Form.html','r',encoding='UTF-8') as TextFile:
            Response_file=TextFile.read()
            Response_file=Response_file.format(Error_code,Error_msg).encode('utf-8')
        self.log(f"[ Handle Error ] ==> Code : \033[35m{Error_code}\033[0m")
        return Error_code,Response_file
    
    def addFormatToHTML(self,HtmlText : str, FormatData : dict, style : str):
        Format=''
        for key,val in FormatData.items():
            Format+=f'{style.format(val=val,key=key)}'
        HtmlText=HtmlText.format(Format=Format)
        return HtmlText

    def SignUp_Handler(self,UserID,UserEmail,UserName,UserPw,is_valid_cookie):
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
        DB=StructDB(UserUID,AuthenticatedName,AuthenticatedPassword,UserEmail)
        self.ServerUsersDB.add(DB)
        self.log(f"[ New DataBase Constructed ] ==> DBID : \033[36m{DB.DataBaseID}\033[0m")
        self.log(f"[ SignUp User ] ==> UUID : \033[96m{UserUID}\033[0m")
        self.HandleSaveDB()
        return self.HandleTextFileRequest('/html/SignUp_Action.html')

    def Login_Handler(self, UserID, UserPw, is_valid_cookie):
        UserUID = uuid.uuid5(uuid.UUID('30076a53-4522-5b28-af4c-b30c260a456d'), UserID)
        # Check if user is already logged in
        if self.Sessions and is_valid_cookie:
            return self.ErrorHandler('403 Forbidden','Warning: You are already logged in. There is no need to log in again. You can continue using the current account.')
        # Check user credentials and create new session
        for db in self.ServerUsersDB:
            if (UserUID == db.UserUID and UserPw == db.UserPw):
                session = self.RegisterUserSession(1, {'UserUID': UserUID, 'DataBaseID':db.DataBaseID, 'UserName':db.UserName})
                self.log(f"[ New Session Constructed ] ==> SessionID: \033[96m{session.SessionToken}\033[0m")
                return self.HandleLoginRequest(session)
        return self.ErrorHandler('422 Unprocessable Entity',f'User ID or password does not exist: {UserID, UserPw}')
    
    def Logout_Handler(self,is_valid_cookie,session):
        if is_valid_cookie:
            self.Sessions.remove(session)
            self.log(f"[ Session Destructed ] ==> SessionID : \033[96m{session.SessionToken}\033[0m")
            return self.HandleLogoutRequest(session)
        return self.ErrorHandler('403 Forbidden',f'To log out, you must first log in. Please verify your account information and log in before attempting to log out')
    
    def HandleAccountFileRequest(self,Request):
        DataBase=self.getDatabase(self.verifySessionCookie(Request)[2].UserInfo['DataBaseID'])
        with open(f'resource/html/Account_Info.html','r',encoding='UTF-8') as TextFile:
            Response_file=TextFile.read()
            Response_file=Response_file.format(UserName=DataBase.UserName,UserUID=DataBase.UserUID,UserPw=DataBase.UserPw,UserEmail=DataBase.UserEmail,BirthDate=DataBase.UserBirthDate).encode('utf-8')
        return '200 OK',Response_file
    
    def UpdateAccount_Handler(self,newUserInfo,session):
        DataBase=self.getDatabase(session.UserInfo['DataBaseID'])
        DataBase.UserName=newUserInfo['UserName']
        DataBase.UserEmail=newUserInfo['UserEmail']
        DataBase.UserBirthDate=newUserInfo['BirthDate']
        if DataBase.UserPw!=newUserInfo['UserPw']:
            DataBase.UserPw=newUserInfo['UserPw']
            self.Logout_Handler(session.SessionToken)   
        self.HandleSaveDB()
        return self.HandleTextFileRequest('/html/Account_Action.html')
    
    def getDatabase(self,DataBaseID):
        for DataBase in self.ServerUsersDB:
            if DataBaseID == DataBase.DataBaseID:
                return DataBase
        
    def UploadPost_Handler(self, PostData, Session):
        if Session is None:
            return self.ErrorHandler('403 Forbidden', 'Warning! You are attempting to post without logging in. If you wish to make a post, please proceed with the login.')

        PostImageName = ''
        User = Session.UserInfo['UserUID']
        UploadTime = datetime.now().strftime('%Y-%m-%d_%H%M')
        post_file_upload_path = f'resource/PostFileUpload/{User}'

        try:
            os.makedirs(post_file_upload_path, exist_ok=True)
        except OSError as e:
            print(f"Error: {e}")

        PostFileName = f'resource/PostFileUpload/{User}/_{UploadTime}.html'.replace(':', '-')
        title = PostData['title']
        content = PostData['content']
        name = Session.UserInfo['UserName']
        image =f'_{UploadTime}.png'

        if PostData['image'] is not None:
            OriginalData = base64.b64decode(PostData['image'])
            PostImageName = f'_{UploadTime}.png'
            with open(f'{post_file_upload_path}/{PostImageName}', 'wb') as ImageFile:
                ImageFile.write(OriginalData)

        with open(f'resource/html/Post_Form.html', 'r', encoding='UTF-8') as PostFormFile:
            with open(PostFileName, 'w', encoding='UTF-8') as PostTempFile:
                PostTempFile.write(PostFormFile.read().format(PostTitle=title, PostContent=content, UserName=name, PostImage=image))
                self.ServerPostDB.append({str(User): {'Path': f'/_{UploadTime}.html', 'title': title, 'content': content, 'name': name}})

        return self.UpdateFeedPage()

    def UpdateFeedPage(self):
        FeedPostForm = """
            <div class="mainform">
                <div class="border rounded-lg p-4 cursor-pointer" onclick="goToPostPage('{0}')">
                    <div class="post">
                        <h2 class="text-lg font-bold mb-2">{1}</h2>
                        <p>{2}</p>
                    </div>
                </div>
            </div>\n"""

        with open(f'resource/html/Feed_Page.html', 'r', encoding='UTF-8') as FeedFormFile:
            FeedForm = FeedFormFile.read()

        FeedPost = ''
        if self.ServerPostDB:
            for i in self.ServerPostDB:
                for ID, Post in i.items():
                    PostFilePath = f'/PostFileUpload/{ID}' + Post['Path'].replace(':', '-')
                    FeedPost += FeedPostForm.format(PostFilePath, Post['title'], Post['content'])

        with open(f'resource/html/PostStorage.html', 'w', encoding='UTF-8') as PostStorage:
            PostStorage.write(FeedPost)

        FeedForm = FeedForm.replace('{FeedPost}', FeedPost).encode('UTF-8')

        return '200 OK', FeedForm

    def RegisterUserSession(self,  SessionValidityDays: str, UserInfo: dict):
        SessionInfo = Session(SessionValidityDays, UserInfo)
        self.Sessions.add(SessionInfo)
        return SessionInfo

    def HandleSaveDB(self):
        with open(f'resource/ServerUserDB.DB','wb') as DBfile:
            pickle.dump(self.ServerUsersDB,DBfile)
            self.log(f"[ Database Save Successful ] ==> path : \033[34mresource/ServerUserDB.DB\033[0m")

    def HandleloadDB(self):
        try:
            with open(f'resource/ServerUserDB.DB','rb') as DBfile:
                self.ServerUsersDB=pickle.load(DBfile)
                self.log(f"[ Database Load Successful ] ==> path : \033[34mresource/ServerUserDB.DB\033[0m")
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
    #SessionDict: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """
        Initializes the SessionToken, SessionValidity, and SessionDict attributes after object creation.
        """
        self.SessionToken = SessionID(16).Token
        self.SessionValidity = HttpDateTime().datetime_to_http_datetime(datetime.now() + timedelta(days=self.SessionValidityDays))
        # self.SessionDict['SessionID'] = self.SessionToken
        # self.SessionDict['SessionValidity'] = self.SessionValidity
        # self.SessionDict['UserInfo'] = self.UserInfo

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