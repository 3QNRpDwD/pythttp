import datetime as dt
import pickle



class DBManager:
    def __init__(self) -> None:
        pass

    def SaveDB(self):
        with open('ServerDB.DB','wb') as WDB:
            pickle.dump(self.ServerDB,WDB)
        return 'Done'
    
    
    def loadDB(self):
        with open('ServerDB.DB','rb') as RDB:
            self.ServerDB=pickle.load(RDB)
        return 'Done'

    def CreatDB(self):
        with open('ServerDB.DB','ab') as CDB:
            pickle.dump(self.ServerDB,CDB)
        return 'Done'

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

    def _response_headers(self,status_code,Content):
        headers = {
            'Date': HttpDateTime().http_date_time,
            'Server':'longinus',
            'Cache-Control': 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0',
            'Pragma' : 'no-cache',
            'Content-Length': len(Content)
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