import datetime as dt
from dataclasses import dataclass, field
import pickle



@dataclass
class StructDB:
    UserUID: str
    UserName: str
    UserPw: str
    UserEmail: str = None
    UserUploadFiles: dict =field(default_factory=dict)
    StructDBdict: dict =field(init=False,default_factory=dict)
    def __post_init__(self):
        self.StructDBdict['UserUID'] = self.UserUID
        self.StructDBdict['UserName'] = self.UserName
        self.StructDBdict['UserPw'] = self.UserPw
        self.StructDBdict['UserEmail'] = self.UserEmail
        self.StructDBdict['UserUploadFiles'] = self.UserUploadFiles


class PrepareHeader:
    def __init__(self, user_agent='127.0.0.1', body=None):
        self.body = body
        self.status_code="HTTP/1.1 200 OK"
        self.string_header = self.status_code + '\r\n'
        self.default_header = {}
        for key, value in self.default_header.items():
            line = f'{key}:{value}'
            self.string_header += line + '\r\n'
        self.string_header += '\r\n'
        
    def _request_headers(self, method: str, url: str, params: dict):
        headers = {
            'Date': HttpDateTime().http_date_time,
            'User-Agent': 'longinus',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'application/json',
        }
        if params:
            url += '?' + '&'.join([f'{key}={value}' for key, value in params.items()])
        return f'{method} {url} HTTP/1.1\r\n' + \
               '\r\n'.join([f'{key}: {value}' for key, value in headers.items()]) + \
               '\r\n\r\n'

    def _response_headers(self,status_code,Content,Cookie=None):
        headers = {
            'Date': HttpDateTime().http_date_time,
            'Server':'longinus',
            'Cache-Control': 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0',
            'Pragma' : 'no-cache',
            'Content-Length': len(Content),
            'Set-Cookie' : Cookie
        }
        return (f'HTTP/1.1 {status_code}\r\n' + \
        '\r\n'.join([f'{key}: {value}' for key, value in headers.items()]) + \
        '\r\n\r\n').encode()

class HttpDateTime:
    def __init__(self):
        now_utc = dt.datetime.utcnow().replace(microsecond=0)
        month_dict = {
            '01': 'Jan',
            '02': 'Feb',
            '03': 'Mar',
            '04': 'Apr',
            '05': 'May',
            '06': 'Jun',
            '07': 'Jul',
            '08': 'Aug',
            '09': 'Sep',
            '10': 'Oct',
            '11': 'Nov',
            '12': 'Dec'
        }
        day_list = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        self.http_date_time = f'{day_list[now_utc.weekday()]} {now_utc.day} {month_dict[now_utc.strftime("%m")]} {now_utc.year} {now_utc.strftime("%H:%M:%S")} GMT'