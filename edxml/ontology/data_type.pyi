# -*- coding: utf-8 -*-
from lxml import etree
from typing import List, Set


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
    # Expression used for matching valid EDXML floats (signed)
    FLOAT_PATTERN_SIGNED = ...
    # Expression used for matching valid EDXML floats (unsigned)
    FLOAT_PATTERN_UNSIGNED = ...
    # Expression used for matching valid EDXML datetime values
    DATETIME_PATTERN = ...

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
    def sequence(cls) -> 'DataType': ...

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
    def currency(cls) -> 'DataType': ...

    @classmethod
    def string(cls, length: int = 0, lower_case: bool = True, upper_case: bool = True, require_unicode: bool = True,
               reverse_storage: bool = False) -> 'DataType': ...

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

    @classmethod
    def ip_v6(cls) -> 'DataType': ...

    def get(self) -> str: ...

    def get_family(self) -> str: ...

    def get_split(self) -> List[str]: ...

    def is_numerical(self) -> bool: ...

    def is_datetime(self) -> bool: ...

    def _generate_schema_datetime(self) -> etree.Element: ...

    def _generate_schema_sequence(self) -> etree.Element: ...

    def _generate_schema_number(self) -> etree.Element: ...

    def _generate_schema_uri(self) -> etree.Element: ...

    def _generate_schema_hex(self) -> etree.Element: ...

    def _generate_schema_uuid(self) -> etree.Element: ...

    def _generate_schema_string(self, regexp: str) -> etree.Element: ...

    def _generate_schema_base64(self) -> etree.Element: ...

    def _generate_schema_boolean(self) -> etree.Element: ...

    def _generate_schema_enum(self) -> etree.Element: ...

    def _generate_schema_ip(self) -> etree.Element: ...

    def _generate_schema_hashlink(self) -> etree.Element: ...

    def _generate_schema_geo(self) -> etree.Element: ...

    def generate_relaxng(self, regexp: str) -> etree.Element: ...

    def _normalize_datetime(self, values) -> Set: ...

    def _normalize_number(self, values) -> Set: ...

    def _normalize_hex(self, values) -> Set: ...

    def _normalize_uri(self, values) -> Set: ...

    def _normalize_ip(self, values) -> Set: ...

    def _normalize_geo(self, values) -> Set: ...

    def _normalize_string(self, values) -> Set: ...

    def _normalize_base64(self, values) -> Set: ...

    def _normalize_boolean(self, values) -> Set: ...

    def normalize_objects(self, value: List[str]) -> List[str]: ...

    def validate_object_value(self, value: str) -> 'DataType': ...

    def _validate_value_datetime(self, value) -> None: ...

    def _validate_value_sequence(self, value) -> None: ...

    def _validate_value_number(self, value) -> None: ...

    def _validate_value_hex(self, value) -> None: ...

    def _validate_value_uuid(self, value) -> None: ...

    def _validate_value_geo(self, value) -> None: ...

    def _validate_value_string(self, value) -> None: ...

    def _validate_value_uri(self, value) -> None: ...

    def _validate_value_base64(self, value) -> None: ...

    def _validate_value_hashlink(self, value) -> None: ...

    def _validate_value_ip(self, value) -> None: ...

    def _validate_value_boolean(self, value) -> None: ...

    def _validate_value_enum(self, value) -> None: ...

    def _validate_decimal(self) -> None: ...

    def _validate_number(self) -> None: ...

    def _validate_hex(self) -> None: ...

    def validate(self) -> 'DataType': ...

    @classmethod
    def format_utc_datetime(cls, date_time: datetime) -> str: ...
