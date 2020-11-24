import grpc
import os
from pprint import pprint

# import the generated classes
import src.tests.definition_pb2 as definition_pb2
import src.tests.definition_pb2_grpc as definition_pb2_grpc

# open a gRPC channel
# channel = grpc.insecure_channel('localhost:8080')


with open('ca.pem', 'rb') as f:
    creds = grpc.ssl_channel_credentials(f.read())
channel = grpc.secure_channel('127.0.0.1:8080', creds, options=(('grpc.ssl_target_name_override', 'foo.test.google.fr'),))


# create a stub (client)
stub = definition_pb2_grpc.FileHandlerAkkaServiceStub(channel)

# create a valid request message
number = definition_pb2.SayHelloMessage(message="hey it's a me")

# make the call
response = stub.Greet(number)

# et voilà
pprint(response.message)


if __name__ == '__main__':
    pass