# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: msg.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'msg.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\tmsg.proto\x12\x13WechatBakTool.Model\")\n\x06TVType\x12\x0c\n\x04Type\x18\x01 \x01(\x05\x12\x11\n\tTypeValue\x18\x02 \x01(\t\"6\n\x08ProtoMsg\x12*\n\x05TVMsg\x18\x03 \x03(\x0b\x32\x1b.WechatBakTool.Model.TVTypeb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'msg_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_TVTYPE']._serialized_start=34
  _globals['_TVTYPE']._serialized_end=75
  _globals['_PROTOMSG']._serialized_start=77
  _globals['_PROTOMSG']._serialized_end=131
# @@protoc_insertion_point(module_scope)
