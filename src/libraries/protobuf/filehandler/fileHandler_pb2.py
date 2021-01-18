# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: fileHandler.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='fileHandler.proto',
  package='',
  syntax='proto3',
  serialized_options=_b('\n\026com.chartsbot.servicesB\020FileHandlerProtoP\001'),
  serialized_pb=_b('\n\x11\x66ileHandler.proto\"\x98\x01\n\x11\x46ileUploadRequest\x12\x0e\n\x06\x63hatId\x18\x01 \x01(\x05\x12\x11\n\tchatTitle\x18\x02 \x01(\t\x12\x1a\n\x12\x66ileClassification\x18\x03 \x01(\t\x12\x10\n\x08\x66ileType\x18\x04 \x01(\t\x12\x0e\n\x06\x61uthor\x18\x05 \x01(\t\x12\x14\n\x0ctimeCreation\x18\x06 \x01(\r\x12\x0c\n\x04\x66ile\x18\x07 \x01(\x0c\"5\n\x12\x46ileUploadResponse\x12\x0e\n\x06status\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"\"\n\x0fSayHelloMessage\x12\x0f\n\x07message\x18\x01 \x01(\t\"^\n\x0e\x46ileGetRequest\x12\x0e\n\x06\x63hatId\x18\x01 \x01(\x05\x12\x1a\n\x12\x66ileClassification\x18\x02 \x01(\t\x12\x10\n\x08\x66ileType\x18\x03 \x01(\t\x12\x0e\n\x06\x61uthor\x18\x05 \x01(\t\"g\n\x0f\x46ileGetResponse\x12\x0e\n\x06status\x18\x01 \x01(\x08\x12\x10\n\x08\x66ileType\x18\x04 \x01(\t\x12\x0e\n\x06\x61uthor\x18\x05 \x01(\t\x12\x14\n\x0ctimeCreation\x18\x06 \x01(\r\x12\x0c\n\x04\x66ile\x18\x07 \x01(\x0c\"_\n\x11\x46ileDeleteRequest\x12\x0e\n\x06\x63hatId\x18\x01 \x01(\x05\x12\x1a\n\x12\x66ileClassification\x18\x03 \x01(\t\x12\x10\n\x08\x66ileType\x18\x04 \x01(\t\x12\x0c\n\x04name\x18\x05 \x01(\t\"5\n\x12\x46ileDeleteResponse\x12\x0e\n\x06status\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t2\xe9\x01\n\x16\x46ileHandlerAkkaService\x12\x37\n\nUploadFile\x12\x12.FileUploadRequest\x1a\x13.FileUploadResponse\"\x00\x12\x37\n\nDeleteFile\x12\x12.FileDeleteRequest\x1a\x13.FileDeleteResponse\"\x00\x12.\n\x07GetFile\x12\x0f.FileGetRequest\x1a\x10.FileGetResponse\"\x00\x12-\n\x05Greet\x12\x10.SayHelloMessage\x1a\x10.SayHelloMessage\"\x00\x42,\n\x16\x63om.chartsbot.servicesB\x10\x46ileHandlerProtoP\x01\x62\x06proto3')
)




_FILEUPLOADREQUEST = _descriptor.Descriptor(
  name='FileUploadRequest',
  full_name='FileUploadRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='chatId', full_name='FileUploadRequest.chatId', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='chatTitle', full_name='FileUploadRequest.chatTitle', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fileClassification', full_name='FileUploadRequest.fileClassification', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fileType', full_name='FileUploadRequest.fileType', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='author', full_name='FileUploadRequest.author', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='timeCreation', full_name='FileUploadRequest.timeCreation', index=5,
      number=6, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='file', full_name='FileUploadRequest.file', index=6,
      number=7, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=22,
  serialized_end=174,
)


_FILEUPLOADRESPONSE = _descriptor.Descriptor(
  name='FileUploadResponse',
  full_name='FileUploadResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='FileUploadResponse.status', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='message', full_name='FileUploadResponse.message', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=176,
  serialized_end=229,
)


_SAYHELLOMESSAGE = _descriptor.Descriptor(
  name='SayHelloMessage',
  full_name='SayHelloMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='message', full_name='SayHelloMessage.message', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=231,
  serialized_end=265,
)


_FILEGETREQUEST = _descriptor.Descriptor(
  name='FileGetRequest',
  full_name='FileGetRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='chatId', full_name='FileGetRequest.chatId', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fileClassification', full_name='FileGetRequest.fileClassification', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fileType', full_name='FileGetRequest.fileType', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='author', full_name='FileGetRequest.author', index=3,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=267,
  serialized_end=361,
)


_FILEGETRESPONSE = _descriptor.Descriptor(
  name='FileGetResponse',
  full_name='FileGetResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='FileGetResponse.status', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fileType', full_name='FileGetResponse.fileType', index=1,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='author', full_name='FileGetResponse.author', index=2,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='timeCreation', full_name='FileGetResponse.timeCreation', index=3,
      number=6, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='file', full_name='FileGetResponse.file', index=4,
      number=7, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=363,
  serialized_end=466,
)


_FILEDELETEREQUEST = _descriptor.Descriptor(
  name='FileDeleteRequest',
  full_name='FileDeleteRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='chatId', full_name='FileDeleteRequest.chatId', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fileClassification', full_name='FileDeleteRequest.fileClassification', index=1,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fileType', full_name='FileDeleteRequest.fileType', index=2,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='name', full_name='FileDeleteRequest.name', index=3,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=468,
  serialized_end=563,
)


_FILEDELETERESPONSE = _descriptor.Descriptor(
  name='FileDeleteResponse',
  full_name='FileDeleteResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='FileDeleteResponse.status', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='message', full_name='FileDeleteResponse.message', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=565,
  serialized_end=618,
)

DESCRIPTOR.message_types_by_name['FileUploadRequest'] = _FILEUPLOADREQUEST
DESCRIPTOR.message_types_by_name['FileUploadResponse'] = _FILEUPLOADRESPONSE
DESCRIPTOR.message_types_by_name['SayHelloMessage'] = _SAYHELLOMESSAGE
DESCRIPTOR.message_types_by_name['FileGetRequest'] = _FILEGETREQUEST
DESCRIPTOR.message_types_by_name['FileGetResponse'] = _FILEGETRESPONSE
DESCRIPTOR.message_types_by_name['FileDeleteRequest'] = _FILEDELETEREQUEST
DESCRIPTOR.message_types_by_name['FileDeleteResponse'] = _FILEDELETERESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

FileUploadRequest = _reflection.GeneratedProtocolMessageType('FileUploadRequest', (_message.Message,), dict(
  DESCRIPTOR = _FILEUPLOADREQUEST,
  __module__ = 'fileHandler_pb2'
  # @@protoc_insertion_point(class_scope:FileUploadRequest)
  ))
_sym_db.RegisterMessage(FileUploadRequest)

FileUploadResponse = _reflection.GeneratedProtocolMessageType('FileUploadResponse', (_message.Message,), dict(
  DESCRIPTOR = _FILEUPLOADRESPONSE,
  __module__ = 'fileHandler_pb2'
  # @@protoc_insertion_point(class_scope:FileUploadResponse)
  ))
_sym_db.RegisterMessage(FileUploadResponse)

SayHelloMessage = _reflection.GeneratedProtocolMessageType('SayHelloMessage', (_message.Message,), dict(
  DESCRIPTOR = _SAYHELLOMESSAGE,
  __module__ = 'fileHandler_pb2'
  # @@protoc_insertion_point(class_scope:SayHelloMessage)
  ))
_sym_db.RegisterMessage(SayHelloMessage)

FileGetRequest = _reflection.GeneratedProtocolMessageType('FileGetRequest', (_message.Message,), dict(
  DESCRIPTOR = _FILEGETREQUEST,
  __module__ = 'fileHandler_pb2'
  # @@protoc_insertion_point(class_scope:FileGetRequest)
  ))
_sym_db.RegisterMessage(FileGetRequest)

FileGetResponse = _reflection.GeneratedProtocolMessageType('FileGetResponse', (_message.Message,), dict(
  DESCRIPTOR = _FILEGETRESPONSE,
  __module__ = 'fileHandler_pb2'
  # @@protoc_insertion_point(class_scope:FileGetResponse)
  ))
_sym_db.RegisterMessage(FileGetResponse)

FileDeleteRequest = _reflection.GeneratedProtocolMessageType('FileDeleteRequest', (_message.Message,), dict(
  DESCRIPTOR = _FILEDELETEREQUEST,
  __module__ = 'fileHandler_pb2'
  # @@protoc_insertion_point(class_scope:FileDeleteRequest)
  ))
_sym_db.RegisterMessage(FileDeleteRequest)

FileDeleteResponse = _reflection.GeneratedProtocolMessageType('FileDeleteResponse', (_message.Message,), dict(
  DESCRIPTOR = _FILEDELETERESPONSE,
  __module__ = 'fileHandler_pb2'
  # @@protoc_insertion_point(class_scope:FileDeleteResponse)
  ))
_sym_db.RegisterMessage(FileDeleteResponse)


DESCRIPTOR._options = None

_FILEHANDLERAKKASERVICE = _descriptor.ServiceDescriptor(
  name='FileHandlerAkkaService',
  full_name='FileHandlerAkkaService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=621,
  serialized_end=854,
  methods=[
  _descriptor.MethodDescriptor(
    name='UploadFile',
    full_name='FileHandlerAkkaService.UploadFile',
    index=0,
    containing_service=None,
    input_type=_FILEUPLOADREQUEST,
    output_type=_FILEUPLOADRESPONSE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='DeleteFile',
    full_name='FileHandlerAkkaService.DeleteFile',
    index=1,
    containing_service=None,
    input_type=_FILEDELETEREQUEST,
    output_type=_FILEDELETERESPONSE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='GetFile',
    full_name='FileHandlerAkkaService.GetFile',
    index=2,
    containing_service=None,
    input_type=_FILEGETREQUEST,
    output_type=_FILEGETRESPONSE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='Greet',
    full_name='FileHandlerAkkaService.Greet',
    index=3,
    containing_service=None,
    input_type=_SAYHELLOMESSAGE,
    output_type=_SAYHELLOMESSAGE,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_FILEHANDLERAKKASERVICE)

DESCRIPTOR.services_by_name['FileHandlerAkkaService'] = _FILEHANDLERAKKASERVICE

# @@protoc_insertion_point(module_scope)
