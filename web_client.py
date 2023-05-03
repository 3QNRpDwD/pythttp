from socket import socket


class HyperTextTransferProtocol:
    def __init__(self):
        self.hyper_text = bytearray()

    def receive(self, max_recv_size=2048):
        while b'\r\n\r\n' not in self.hyper_text:
            self.hyper_text += self.socket.recv(max_recv_size)
        return self.hyper_text

    def get(self, url: str, port: int = 80, params: dict = None):
        try:
            self.socket = socket()
            self.socket.connect((url, port))
            headers = self._prepare_request_headers('GET', url, params)
            self.socket.send(headers.encode())
            #return self.receive()
        except ConnectionRefusedError as e:
            print(f'Request to server failed... Reason: {e}')
        finally:
            self.socket.close()

    def post(self):
        pass

    def _prepare_request_headers(self, method: str, url: str, params: dict):
        headers = {
            'Date': '',
            'User-Agent': 'longinuspypialpha',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'application/json',
        }
        if params:
            url += '?' + '&'.join([f'{key}={value}' for key, value in params.items()])
        return f'{method} {url} HTTP/1.1\r\n' + \
               '\r\n'.join([f'{key}: {value}' for key, value in headers.items()]) + \
               '\r\n\r\n'

def request2():

    while True:
        user_input = input('Request : ') # example : [method *Currently, only the GET method is supported. ] [domain or server addres]  [key=value]
        tokens = user_input.split(' ')

        if tokens[0].upper() == 'GET':
            url = tokens[1]
            params = None

            if len(tokens) > 2:
                params = {}

                for token in tokens[2:]:
                    param = token.split('=')

                    if len(param) == 2:
                        params[param[0]] = param[1]

            try:
                response = None
                response = HyperTextTransferProtocol().get(url=url, params=params)
                print(response.decode())
            except ConnectionError:
                print('Connection error. Please try again.')
        else:
            print('Invalid request.')
a=1
while True:
    HyperTextTransferProtocol().get(url='127.0.0.1')
    print(a)
    a+=1
    
            