# -*- coding: utf-8 -*-
from lxml import etree
from typing import List


class DataType(object):

    # Expression used for matching SHA1 hashlinks
    HASHLINK_PATTERN = ...
    # Expression used for matching string datatypes
    STRING_PATTERN = ...
    # Expression used for matching base64 datatypes
    BASE64_PATTERN = ...
    # Expression used for matching uri datatypes
    URI_PATTERN = ...
    # Expression used for matching uuid datatypes
    UUID_PATTERN = ...

    FAMILY_DATETIME = ...
    FAMILY_SEQUENCE = ...
    FAMILY_NUMBER = ...
    FAMILY_HEX = ...
    FAMILY_UUID = ...
    FAMILY_BOOLEAN = ...
    FAMILY_STRING = ...
    FAMILY_BASE64 = ...
    FAMILY_URI = ...
    FAMILY_ENUM = ...
    FAMILY_GEO = ...
    FAMILY_IP = ...
    FAMILY_HASHLINK = ...

    def __init__(self, data_type: str) -> None:

        self.type = ...  # type: str

    @classmethod
    def datetime(cls) -> 'DataType': ...

    @classmethod
    def boolean(cls) -> 'DataType': ...

    @classmethod
    def tiny_int(cls, signed: bool = True) -> 'DataType': ...

    @classmethod
    def small_int(cls, signed: bool = True) -> 'DataType': ...

    @classmethod
    def medium_int(cls, signed: bool = True) -> 'DataType': ...

    @classmethod
    def int(cls, signed: bool = True) -> 'DataType': ...

    @classmethod
    def big_int(cls, signed: bool = True) -> 'DataType': ...

    @classmethod
    def float(cls, signed: bool = True) -> 'DataType': ...

    @classmethod
    def double(cls, signed=True) -> 'DataType': ...

    @classmethod
    def decimal(cls, total_digits: int, fractional_digits: int, signed: bool = True) -> 'DataType': ...

    @classmethod
    def string(cls, length: int = 0, case_sensitive: bool = True, require_unicode: bool = True, reverse_storage: bool = False) -> 'DataType': ...

    @classmethod
    def base64(cls, length: int = 0) -> 'DataType': ...

    @classmethod
    def enum(cls, *choices: str) -> 'DataType': ...

    @classmethod
    def uri(cls, path_separator: str = '/') -> 'DataType': ...

    @classmethod
    def hex(cls, length: int, separator: str = None, group_size: int = None) -> 'DataType': ...

    @classmethod
    def uuid(cls) -> 'DataType': ...

    @classmethod
    def geo_point(cls) -> 'DataType': ...

    @classmethod
    def hashlink(cls) -> 'DataType': ...

    @classmethod
    def ip_v4(cls) -> 'DataType': ...

    def get(self) -> str: ...

    def get_family(self) -> str: ...

    def get_split(self) -> List[str]: ...

    def is_numerical(self) -> bool: ...

    def is_datetime(self) -> bool: ...

    def generate_relaxng(self, regexp: str) -> etree.Element: ...

    def normalize_objects(self, value: List[unicode]) -> List[unicode]: ...

    def validate_object_value(self, value: unicode) -> 'DataType': ...

    def validate(self) -> 'DataType': ...

    @classmethod
    def format_utc_datetime(cls, date_time: datetime) -> str: ...
