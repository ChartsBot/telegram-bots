import grpc
import os
from pprint import pprint

# import the generated classes
import src.libraries.protobuf.filehandler.fileHandler_pb2 as filehandler_pb2
import src.libraries.protobuf.filehandler.fileHandler_pb2_grpc as filehandler_pb2_grpc

# open a gRPC channel
# channel = grpc.insecure_channel('localhost:8080')

with open('ca.pem', 'rb') as f:
    creds = grpc.ssl_channel_credentials(f.read())
channel = grpc.secure_channel('127.0.0.1:8080', creds,
                              options=(('grpc.ssl_target_name_override', 'foo.test.google.fr'),))

# create a stub (client)
stub = filehandler_pb2_grpc.FileHandlerAkkaServiceStub(channel)

# create a valid request message
number = filehandler_pb2.SayHelloMessage(message="hey it's a me")

# make the call
response = stub.Greet(number)

# et voilà
pprint(response.message)

imgpath = "/home/ben/Crypto/tg-bots/telegram-bots/src/libraries/testaaa2.png"
img2 = "/home/ben/Crypto/tg-bots/telegram-bots/src/tests/pil_text.png"

file = filehandler_pb2.FileUploadRequest(chatId=12345,
                                         chatTitle="test",
                                         fileClassification="meme",
                                         fileType="image",
                                         author="ben",
                                         timeCreation=1,
                                         pathOnDisk=img2)

response = stub.UploadFile(file)

pprint(response)

if __name__ == '__main__':
    pass
