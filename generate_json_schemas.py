#!/usr/bin/env python3
"""
UBL 2.5 JSON Schema Generator

Reads Genericode (GC) XML files and generates JSON Schema files for:
- UnqualifiedDataTypes
- QualifiedDataTypes
- CommonBasicComponents
- CommonAggregateComponents
- CommonExtensionComponents
- Signature components
- Document schemas
"""

import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# Version suffix for generated schema filenames.
# Filenames use the full version "-2.5" to match XML specification naming.
FILE_VERSION_SUFFIX = '-2.5'

# URN base for JSON schema identifiers, paralleling the XSD convention:
#   XSD:  urn:oasis:names:specification:ubl:schema:xsd:Invoice-2
#   JSON: urn:oasis:names:specification:ubl:schema:json:Invoice-2
# URNs are stable at the major version level ("-2", not "-2.5").
URN_BASE = 'urn:oasis:names:specification:ubl:schema:json'


def parse_gc_file(filepath):
    """
    Parse a Genericode XML file and extract all rows as dicts.

    Args:
        filepath: Path to the GC file

    Returns:
        List of dicts, each representing a row with ColumnRef keys

    Note:
        The Row and Value elements are in NO namespace (default).
        Only the root gc:CodeList has the gc namespace.
    """
    rows = []

    tree = ET.parse(filepath)
    root = tree.getroot()

    # Define namespace for gc: prefix
    namespaces = {
        'gc': 'http://docs.oasis-open.org/codelist/ns/genericode/1.0/'
    }

    # Find SimpleCodeList under gc namespace
    simple_code_list = root.find('SimpleCodeList', namespaces)
    if simple_code_list is None:
        # Fallback: try without namespace
        simple_code_list = root.find('SimpleCodeList')

    if simple_code_list is not None:
        # Row elements are in default namespace (no prefix)
        for row in simple_code_list.findall('Row'):
            row_dict = {}

            # Value elements are in default namespace
            for value in row.findall('Value'):
                column_ref = value.get('ColumnRef')
                if column_ref:
                    # SimpleValue is in default namespace
                    simple_value = value.find('SimpleValue')
                    if simple_value is not None and simple_value.text:
                        row_dict[column_ref] = simple_value.text

            if row_dict:
                rows.append(row_dict)

    return rows


def build_registry(rows):
    """
    Build a structured registry from parsed GC rows.

    Groups rows by ModelName and builds a hierarchy:
    - ABIEs as top-level components
    - BBIEs and ASBIEs as children of their ObjectClass (ABIE)

    Args:
        rows: List of dicts from parse_gc_file

    Returns:
        Dict with structure:
        {
            'models': {
                'ModelName': {
                    'abies': {
                        'ObjectClass': {
                            'component_name': str,
                            'definition': str,
                            'children': [...]
                        }
                    }
                }
            }
        }
    """
    registry = {'models': defaultdict(lambda: {'abies': {}})}

    # First pass: collect all rows by model and object class
    model_data = defaultdict(lambda: {'abies': {}, 'children': defaultdict(list)})

    for row in rows:
        model_name = row.get('ModelName')
        component_type = row.get('ComponentType')
        object_class = row.get('ObjectClass')

        if not model_name:
            continue

        # Use ComponentName if available, fall back to UBLName (for signature/extension)
        component_name = row.get('ComponentName') or row.get('UBLName')

        if component_type == 'ABIE':
            # Store ABIE info
            model_data[model_name]['abies'][object_class] = {
                'component_name': component_name,
                'definition': row.get('Definition', ''),
                'dictionary_entry_name': row.get('DictionaryEntryName', ''),
            }
        elif component_type in ('BBIE', 'ASBIE') and object_class:
            # Store as child of the owning ABIE
            child_info = {
                'component_name': component_name,
                'component_type': component_type,
                'cardinality': row.get('Cardinality', ''),
                'definition': row.get('Definition', ''),
            }

            # Add type-specific fields
            if component_type == 'BBIE':
                child_info['representation_term'] = row.get('RepresentationTerm', '')
                child_info['data_type'] = row.get('DataType', '')
            elif component_type == 'ASBIE':
                child_info['associated_object_class'] = row.get('AssociatedObjectClass', '')

            model_data[model_name]['children'][object_class].append(child_info)

    # Second pass: build final registry with children attached to ABIEs
    for model_name, data in model_data.items():
        abies_dict = {}
        for object_class, abie_info in data['abies'].items():
            abie_info['children'] = data['children'].get(object_class, [])
            abies_dict[object_class] = abie_info

        registry['models'][model_name] = {'abies': abies_dict}

    # Convert defaultdict to regular dict
    registry['models'] = dict(registry['models'])

    return registry


# ============================================================================
# Step 3: Generate UnqualifiedDataTypes-2.json
# ============================================================================

def generate_unqualified_data_types(output_dir):
    """
    Generate the UnqualifiedDataTypes-2.json schema.

    Creates a JSON Schema file with definitions for the 14 unqualified data types
    specified in the UBL 2.5 JSON Syntax Binding.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define the 14 unqualified data types with their schemas
    defs = {}

    # ---------------------------------------------------------------
    # Data types follow the DocBook Table T-UBL-UNQUALIFIED-DATA-TYPES
    # which prescribes one supplementary component per type.  The full
    # CCTS attribute sets from the XSD are simplified to the single
    # attribute listed in the DocBook specification.
    # ---------------------------------------------------------------

    # Scalar-only types (no supplementary components)
    defs['DateType'] = {
        'type': 'string',
        'pattern': '^[0-9]{4}-[0-9]{2}-[0-9]{2}$',
        'description': 'One calendar day according the Gregorian calendar.'
    }

    # TimeType: supports optional fractional seconds to match xsd:time
    defs['TimeType'] = {
        'type': 'string',
        'pattern': r'^[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})?$',
        'description': 'An instance of time that occurs every day.'
    }

    defs['IndicatorType'] = {
        'type': 'boolean',
        'description': 'A list of two mutually exclusive Boolean values that express the only possible states of a property.'
    }

    defs['NumericType'] = {
        'type': 'number',
        'description': 'Numeric information that is assigned or is determined by calculation, counting, or sequencing. It does not require a unit of quantity or unit of measure.'
    }

    defs['PercentType'] = {
        'type': 'number',
        'description': 'Numeric information that is assigned or is determined by calculation, counting, or sequencing and is expressed as a percentage. It does not require a unit of quantity or unit of measure.'
    }

    defs['RateType'] = {
        'type': 'number',
        'description': 'A numeric expression of a rate that is assigned or is determined by calculation, counting, or sequencing. It does not require a unit of quantity or unit of measure.'
    }

    # Shorthand helpers – enforce minLength:1 on every string property
    # to satisfy DocBook Section 7.4: "Validation shall fail when …
    # a property is present with an empty string as its value."
    _str = {'type': 'string', 'minLength': 1}
    _num = {'type': 'number'}

    # Mandatory supplementary types (always object form)
    # DocBook Table T-UBL-UNQUALIFIED-DATA-TYPES: one supplementary per type
    defs['AmountType'] = {
        'type': 'object',
        'properties': {
            'value': _num,
            'currencyID': _str
        },
        'required': ['value', 'currencyID'],
        'additionalProperties': False,
        'description': 'A number of monetary units specified using a given unit of currency.'
    }

    # DocBook Section 10.2: mimeCode is mandatory
    defs['BinaryObjectType'] = {
        'type': 'object',
        'properties': {
            'value': _str,
            'mimeCode': _str
        },
        'required': ['value', 'mimeCode'],
        'additionalProperties': False,
        'description': 'A set of finite-length sequences of binary octets.'
    }

    defs['MeasureType'] = {
        'type': 'object',
        'properties': {
            'value': _num,
            'unitCode': _str
        },
        'required': ['value', 'unitCode'],
        'additionalProperties': False,
        'description': 'A numeric value determined by measuring an object using a specified unit of measure.'
    }

    # Optional supplementary types (oneOf scalar or object)
    # DocBook Table T-UBL-UNQUALIFIED-DATA-TYPES prescribes one
    # supplementary component per type.  When no supplementary
    # attribute is present the simple form (bare string/number) is
    # used; when the attribute is present the object form is used.

    defs['CodeType'] = {
        'oneOf': [
            _str,
            {
                'type': 'object',
                'properties': {
                    'value': _str,
                    'listID': _str
                },
                'required': ['value'],
                'additionalProperties': False
            }
        ],
        'description': 'A character string (letters, figures, or symbols) that for brevity and/or language independence may be used to represent or replace a definitive value or text of an attribute, together with relevant supplementary information.'
    }

    defs['IdentifierType'] = {
        'oneOf': [
            _str,
            {
                'type': 'object',
                'properties': {
                    'value': _str,
                    'schemeID': _str
                },
                'required': ['value'],
                'additionalProperties': False
            }
        ],
        'description': 'A character string to identify and uniquely distinguish one instance of an object in an identification scheme from all other objects in the same scheme, together with relevant supplementary information.'
    }

    defs['QuantityType'] = {
        'oneOf': [
            _num,
            {
                'type': 'object',
                'properties': {
                    'value': _num,
                    'unitCode': _str
                },
                'required': ['value'],
                'additionalProperties': False
            }
        ],
        'description': 'A counted number of non-monetary units, possibly including a fractional part.'
    }

    defs['TextType'] = {
        'oneOf': [
            _str,
            {
                'type': 'object',
                'properties': {
                    'value': _str,
                    'languageID': _str
                },
                'required': ['value'],
                'additionalProperties': False
            }
        ],
        'description': 'A character string (i.e. a finite set of characters), generally in the form of words of a language.'
    }

    defs['NameType'] = {
        'oneOf': [
            _str,
            {
                'type': 'object',
                'properties': {
                    'value': _str,
                    'languageID': _str
                },
                'required': ['value'],
                'additionalProperties': False
            }
        ],
        'description': 'A character string that constitutes the distinctive designation of a person, place, thing or concept.'
    }

    # ContentType is used in UBL-CommonExtensionComponents for extension content
    # Maps to xsd:any — an open JSON object
    # DocBook Section 6.3: ExtensionContent "shall not be empty"
    defs['ContentType'] = {
        'type': 'object',
        'minProperties': 1,
        'description': 'Extension content. Any structure is allowed.'
    }

    # Build the complete schema
    schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': f'{URN_BASE}:UnqualifiedDataTypes-2',
        'description': 'UBL 2.5 Unqualified Data Types',
        '$defs': defs
    }

    # Write the schema to file
    output_file = output_dir / f'UnqualifiedDataTypes{FILE_VERSION_SUFFIX}.json'
    with open(output_file, 'w') as f:
        json.dump(schema, f, indent=2)
        f.write('\n')

    print(f"  Written UnqualifiedDataTypes{FILE_VERSION_SUFFIX}.json")


# ============================================================================
# Step 4: Generate QualifiedDataTypes-2.json
# ============================================================================

def generate_qualified_data_types(output_dir, rows):
    """
    Generate the QualifiedDataTypes-2.json schema.

    Args:
        output_dir: Output directory for schemas
        rows: Parsed GC rows

    Creates a JSON Schema file with references to unqualified data types for each
    distinct qualified data type found in the GC rows.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract all unique DataType values from rows
    data_types = set()
    for row in rows:
        if 'DataType' in row:
            data_types.add(row['DataType'])

    defs = {}

    # For each qualified data type, create a $ref to the unqualified base type
    for qualified_type in sorted(data_types):
        # Extract the base type from the qualified type
        # Pattern: "Type Name_ Code. Type" -> extract "Code" -> "CodeType"
        # "Amount. Type" -> extract "Amount" -> "AmountType"
        # "Binary Object. Type" -> extract "Binary Object" -> "BinaryObjectType"

        # Remove ". Type" suffix
        without_suffix = qualified_type.replace('. Type', '')

        # Split by "_ " to get the last part (after underscore-space)
        parts = without_suffix.split('_ ')
        base_name = parts[-1] if parts else without_suffix

        # Derive the unqualified base type by removing spaces and appending Type
        # "Binary Object" -> "BinaryObjectType"
        # "Code" -> "CodeType"
        unqualified_type = base_name.replace(' ', '') + 'Type'

        # Create the key for the defs dict
        # Remove all spaces and handle underscores: "Binary Object" -> "BinaryObject"
        # "Allowance Charge Reason_ Code" -> "AllowanceChargeReasonCode"
        key_name = without_suffix.replace('_ ', '_').replace(' ', '')
        key = key_name + 'Type'

        # Create the reference entry
        defs[key] = {
            '$ref': f'{URN_BASE}:UnqualifiedDataTypes-2#/$defs/{unqualified_type}'
        }

    # Build the complete schema
    schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': f'{URN_BASE}:QualifiedDataTypes-2',
        'description': 'UBL 2.5 Qualified Data Types',
        '$defs': defs
    }

    # Write the schema to file
    output_file = output_dir / f'QualifiedDataTypes{FILE_VERSION_SUFFIX}.json'
    with open(output_file, 'w') as f:
        json.dump(schema, f, indent=2)
        f.write('\n')

    print(f"  Written QualifiedDataTypes{FILE_VERSION_SUFFIX}.json")


# ============================================================================
# Step 5: Generate CommonBasicComponents-2.json
# ============================================================================

def generate_common_basic_components(output_dir, registry):
    """
    Generate the CommonBasicComponents-2.json schema.

    Args:
        output_dir: Output directory for schemas
        registry: Built registry from build_registry()

    Generates a schema that defines every distinct BBIE (Basic Business Information Entity)
    name used across all UBL models, serving as a BBIE type database for constructing documents.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all unique BBIEs across all models
    bbies = {}  # component_name -> data_type

    for model_name, model_data in registry['models'].items():
        for abie_name, abie_info in model_data['abies'].items():
            # Iterate through children of this ABIE
            for child in abie_info.get('children', []):
                # Only process BBIEs, skip ASBIEs
                if child.get('component_type') != 'BBIE':
                    continue

                component_name = child.get('component_name')
                data_type = child.get('data_type')

                # Skip if component_name or data_type is missing
                if not component_name or not data_type:
                    continue

                # Store the first occurrence (they should all be the same)
                if component_name not in bbies:
                    bbies[component_name] = data_type

    # Build $defs entries
    defs = {}

    for component_name in sorted(bbies.keys()):
        data_type = bbies[component_name]

        # Convert data_type to qualified type key
        # Same logic as Step 4:
        # - Remove ". Type" suffix
        # - Split by "_ " and take the last part
        # - Remove all spaces except underscores
        # - Append "Type"

        # Remove ". Type" suffix
        without_suffix = data_type.replace('. Type', '')

        # Split by "_ " to get the last part (after underscore-space)
        parts = without_suffix.split('_ ')
        base_name = parts[-1] if parts else without_suffix

        # Derive the key name by removing spaces and handling underscores
        # "Binary Object" -> "BinaryObject"
        # "Allowance Charge Reason_ Code" -> "AllowanceChargeReasonCode"
        key_name = without_suffix.replace('_ ', '_').replace(' ', '')
        qualified_type_key = key_name + 'Type'

        # Create the $ref entry
        defs[component_name] = {
            '$ref': f'{URN_BASE}:QualifiedDataTypes-2#/$defs/{qualified_type_key}'
        }

    # Build the complete schema
    schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': f'{URN_BASE}:CommonBasicComponents-2',
        'description': 'UBL 2.5 Common Basic Components',
        '$defs': defs
    }

    # Write the schema to file
    output_file = output_dir / f'CommonBasicComponents{FILE_VERSION_SUFFIX}.json'
    with open(output_file, 'w') as f:
        json.dump(schema, f, indent=2)
        f.write('\n')

    print(f"  Written CommonBasicComponents{FILE_VERSION_SUFFIX}.json")


# ============================================================================
# Step 6: Generate CommonAggregateComponents-2.json
# ============================================================================

def generate_common_aggregate_components(output_dir, registry):
    """
    Generate the CommonAggregateComponents-2.json schema.

    Args:
        output_dir: Output directory for schemas
        registry: Built registry from build_registry()

    Generates the ABIE type database containing all 310+ ABIEs from the
    UBL-CommonLibrary-2.5 model in the registry.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get the CommonLibrary ABIEs
    common_library_abies = registry['models'].get('UBL-CommonLibrary-2.5', {}).get('abies', {})

    if not common_library_abies:
        print(f"  No ABIEs found in UBL-CommonLibrary-2.5 model")
        return

    # Build ObjectClass -> TypeName lookup for all ABIEs in CommonLibrary
    object_class_to_type = {}
    for object_class, abie in common_library_abies.items():
        component_name = abie['component_name']
        type_name = component_name + 'Type'
        object_class_to_type[object_class] = type_name

    # Build $defs entries for each ABIE
    defs = {}

    for object_class in sorted(common_library_abies.keys()):
        abie = common_library_abies[object_class]
        component_name = abie['component_name']
        definition = abie.get('definition', '')
        children = abie.get('children', [])

        type_name = component_name + 'Type'

        # Build properties and required list
        properties = {}
        required = []

        # $jsonschema: identifies this ABIE type for standalone use
        # (optional when embedded, required when used as root payload)
        properties['$jsonschema'] = {
            'const': f'{URN_BASE}:CommonAggregateComponents-2#{type_name}',
            'description': 'Identifies the JSON schema governing this instance.'
        }

        for child in children:
            child_component_name = child['component_name']
            component_type = child['component_type']
            cardinality = child['cardinality']

            if component_type == 'BBIE':
                # BBIE: reference to CommonBasicComponents
                ref_schema = {
                    '$ref': f'{URN_BASE}:CommonBasicComponents-2#/$defs/{child_component_name}'
                }

                if cardinality in ('0..1', '1'):
                    properties[child_component_name] = ref_schema
                elif cardinality in ('0..n', '1..n'):
                    # Repeating BBIE: allow single value or array
                    properties[child_component_name] = {
                        'oneOf': [
                            ref_schema,
                            {
                                'type': 'array',
                                'items': ref_schema
                            }
                        ]
                    }
                    if cardinality == '1..n':
                        properties[child_component_name]['oneOf'][1]['minItems'] = 1
                else:
                    properties[child_component_name] = ref_schema

            elif component_type == 'ASBIE':
                # ASBIE: reference to another ABIE (in this schema)
                associated_object_class = child.get('associated_object_class', '')

                # Look up the type name from the object_class_to_type mapping
                if associated_object_class in object_class_to_type:
                    target_type = object_class_to_type[associated_object_class]
                else:
                    # Fallback: replace spaces with empty string and append Type
                    target_type = associated_object_class.replace(' ', '') + 'Type'

                ref_schema = {'$ref': f'#/$defs/{target_type}'}

                if cardinality in ('0..1', '1'):
                    # Single value
                    properties[child_component_name] = ref_schema
                elif cardinality in ('0..n', '1..n'):
                    # Array (single or array)
                    properties[child_component_name] = {
                        'oneOf': [
                            ref_schema,
                            {
                                'type': 'array',
                                'items': ref_schema
                            }
                        ]
                    }
                    # For 1..n, add minItems constraint
                    if cardinality == '1..n':
                        properties[child_component_name]['oneOf'][1]['minItems'] = 1
                else:
                    # Fallback for unknown cardinality
                    properties[child_component_name] = ref_schema

            # Add to required list if cardinality is 1 or 1..n
            if cardinality in ('1', '1..n'):
                required.append(child_component_name)

        # Every ABIE allows an optional UBLExtensions property,
        # matching the xsd:element ref="ext:UBLExtensions" minOccurs="0"
        # that appears in every XSD complex type.
        properties['UBLExtensions'] = {
            '$ref': f'{URN_BASE}:CommonExtensionComponents-2#/$defs/UBLExtensionsType'
        }

        # Build the ABIE definition
        # minProperties:1 per DocBook Section 7.4 (empty objects are invalid)
        dictionary_entry_name = abie.get('dictionary_entry_name', '')
        abie_def = {
            '$anchor': type_name,
            'type': 'object',
            'description': definition,
            'properties': properties,
            'additionalProperties': False,
            'minProperties': 1
        }

        if dictionary_entry_name:
            abie_def['title'] = dictionary_entry_name

        # Add required only if there are required properties
        if required:
            abie_def['required'] = required

        defs[type_name] = abie_def

    # Build the complete schema
    schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': f'{URN_BASE}:CommonAggregateComponents-2',
        'description': 'UBL 2.5 Common Aggregate Components',
        '$defs': defs
    }

    # Write the schema to file
    output_file = output_dir / f'CommonAggregateComponents{FILE_VERSION_SUFFIX}.json'
    with open(output_file, 'w') as f:
        json.dump(schema, f, indent=2)
        f.write('\n')

    print(f"  Written CommonAggregateComponents{FILE_VERSION_SUFFIX}.json with {len(defs)} ABIE types")


# ============================================================================
# Step 7: Generate CommonExtensionComponents-2.json
# ============================================================================

def generate_common_extension_components(output_dir, registry):
    """
    Generate the CommonExtensionComponents-2.json schema.

    Args:
        output_dir: Output directory for schemas
        registry: Built registry from build_registry()

    Generates the CommonExtensionComponents-2.json schema defining UBLExtensions
    as an array of extension objects that can be used for private extensions.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get the extension ABIEs from the registry
    extension_model = registry['models'].get('UBL-CommonExtensionComponents-2.5', {})
    extension_abies = extension_model.get('abies', {})

    if not extension_abies:
        print(f"  No ABIEs found in UBL-CommonExtensionComponents-2.5 model")
        return

    # Find the UBL Extension ABIE
    ubl_extension_abie = None
    for object_class, abie in extension_abies.items():
        if abie.get('component_name') == 'UBLExtension':
            ubl_extension_abie = abie
            break

    if not ubl_extension_abie:
        print(f"  UBLExtension ABIE not found in registry")
        return

    children = ubl_extension_abie.get('children', [])
    definition = ubl_extension_abie.get('definition', '')

    # Build properties and required list for UBLExtensionType
    extension_properties = {}
    extension_required = []

    for child in children:
        child_component_name = child['component_name']
        cardinality = child['cardinality']

        if child_component_name == 'ExtensionContent':
            # ExtensionContent is special: reference to ContentType in UnqualifiedDataTypes
            extension_properties[child_component_name] = {
                '$ref': f'{URN_BASE}:UnqualifiedDataTypes-2#/$defs/ContentType'
            }
        else:
            # All other BBIEs reference CommonBasicComponents
            extension_properties[child_component_name] = {
                '$ref': f'{URN_BASE}:CommonBasicComponents-2#/$defs/{child_component_name}'
            }

        # Add to required list if cardinality is 1
        if cardinality == '1':
            extension_required.append(child_component_name)

    # DocBook Section 6.3: "Each extension shall be a JSON object
    # containing at least the following members: ExtensionURI ... ExtensionContent"
    if 'ExtensionURI' not in extension_required:
        extension_required.append('ExtensionURI')

    # Build $defs
    defs = {}

    # UBLExtensionsType: array of extension objects
    defs['UBLExtensionsType'] = {
        'type': 'array',
        'items': {'$ref': '#/$defs/UBLExtensionType'},
        'minItems': 1
    }

    # UBLExtensionType: single extension object
    dictionary_entry_name = ubl_extension_abie.get('dictionary_entry_name', '')
    ubl_extension_type_def = {
        'type': 'object',
        'description': definition,
        'properties': extension_properties,
        'additionalProperties': False,
        'minProperties': 1
    }

    if dictionary_entry_name:
        ubl_extension_type_def['title'] = dictionary_entry_name

    # Add required only if there are required properties
    if extension_required:
        ubl_extension_type_def['required'] = extension_required

    defs['UBLExtensionType'] = ubl_extension_type_def

    # Build the complete schema
    schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': f'{URN_BASE}:CommonExtensionComponents-2',
        'description': 'UBL 2.5 Common Extension Components',
        '$defs': defs
    }

    # Write the schema to file
    output_file = output_dir / f'CommonExtensionComponents{FILE_VERSION_SUFFIX}.json'
    with open(output_file, 'w') as f:
        json.dump(schema, f, indent=2)
        f.write('\n')

    print(f"  Written CommonExtensionComponents{FILE_VERSION_SUFFIX}.json")


# ============================================================================
# Step 8: Generate Signature schemas
# ============================================================================

def generate_signature_schemas(output_dir, registry):
    """
    Generate signature-related JSON schemas.

    Args:
        output_dir: Output directory for schemas
        registry: Built registry from build_registry()

    Generates two schemas:
    - SignatureBasicComponents-2.json: BBIEs for signature components
    - SignatureAggregateComponents-2.json: ABIEs for signature structures
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate SignatureBasicComponents-2.json
    # Collect all BBIEs from signature models
    signature_bbies = {}  # component_name -> data_type

    signature_models = ['UBL-CommonSignatureComponents-2.5', 'UBL-SignatureLibrary-2.5']

    for model_name in signature_models:
        model_data = registry['models'].get(model_name, {})
        abies = model_data.get('abies', {})

        for abie_name, abie_info in abies.items():
            children = abie_info.get('children', [])

            for child in children:
                if child.get('component_type') != 'BBIE':
                    continue

                component_name = child.get('component_name')
                data_type = child.get('data_type')

                if not component_name or not data_type:
                    continue

                # Store the first occurrence
                if component_name not in signature_bbies:
                    signature_bbies[component_name] = data_type

    # Build $defs for SignatureBasicComponents
    sig_basic_defs = {}

    for component_name in sorted(signature_bbies.keys()):
        data_type = signature_bbies[component_name]

        # Convert data_type to qualified type key using the same logic as Step 4
        without_suffix = data_type.replace('. Type', '')
        parts = without_suffix.split('_ ')
        base_name = parts[-1] if parts else without_suffix
        key_name = without_suffix.replace('_ ', '_').replace(' ', '')
        qualified_type_key = key_name + 'Type'

        # Create the $ref entry to QualifiedDataTypes
        sig_basic_defs[component_name] = {
            '$ref': f'{URN_BASE}:QualifiedDataTypes-2#/$defs/{qualified_type_key}'
        }

    # Build SignatureBasicComponents schema
    sig_basic_schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': f'{URN_BASE}:SignatureBasicComponents-2',
        'description': 'UBL 2.5 Signature Basic Components',
        '$defs': sig_basic_defs
    }

    # Write SignatureBasicComponents
    sig_basic_file = output_dir / f'SignatureBasicComponents{FILE_VERSION_SUFFIX}.json'
    with open(sig_basic_file, 'w') as f:
        json.dump(sig_basic_schema, f, indent=2)
        f.write('\n')

    print(f"  Written SignatureBasicComponents{FILE_VERSION_SUFFIX}.json")

    # Step 2: Generate SignatureAggregateComponents-2.json
    # Get ABIEs from signature models
    sig_agg_defs = {}

    # Process UBL-CommonSignatureComponents-2.5 for UBLDocumentSignatures
    common_sig_model = registry['models'].get('UBL-CommonSignatureComponents-2.5', {})
    common_sig_abies = common_sig_model.get('abies', {})

    for object_class, abie in common_sig_abies.items():
        component_name = abie.get('component_name')
        definition = abie.get('definition', '')
        children = abie.get('children', [])

        if component_name == 'UBLDocumentSignatures':
            type_name = component_name + 'Type'
            properties = {}
            required = []

            # $jsonschema for standalone use
            properties['$jsonschema'] = {
                'const': f'{URN_BASE}:SignatureAggregateComponents-2#{type_name}',
                'description': 'Identifies the JSON schema governing this instance.'
            }

            for child in children:
                child_component_name = child['component_name']
                component_type = child.get('component_type')
                cardinality = child.get('cardinality')

                if component_type == 'ASBIE':
                    # Reference to SignatureInformationType
                    ref_schema = {'$ref': '#/$defs/SignatureInformationType'}

                    if cardinality in ('0..1', '1'):
                        # Single value
                        properties[child_component_name] = ref_schema
                    elif cardinality in ('0..n', '1..n'):
                        # Array (single or array)
                        properties[child_component_name] = {
                            'oneOf': [
                                ref_schema,
                                {
                                    'type': 'array',
                                    'items': ref_schema
                                }
                            ]
                        }
                        # For 1..n, add minItems constraint
                        if cardinality == '1..n':
                            properties[child_component_name]['oneOf'][1]['minItems'] = 1

                # Add to required list if cardinality is 1 or 1..n
                if cardinality in ('1', '1..n'):
                    required.append(child_component_name)

            # Build the ABIE definition
            dictionary_entry_name = abie.get('dictionary_entry_name', '')
            abie_def = {
                '$anchor': type_name,
                'type': 'object',
                'description': definition,
                'properties': properties,
                'additionalProperties': False,
                'minProperties': 1
            }

            if dictionary_entry_name:
                abie_def['title'] = dictionary_entry_name

            if required:
                abie_def['required'] = required

            sig_agg_defs[type_name] = abie_def

    # Process UBL-SignatureLibrary-2.5 for SignatureInformation
    sig_lib_model = registry['models'].get('UBL-SignatureLibrary-2.5', {})
    sig_lib_abies = sig_lib_model.get('abies', {})

    for object_class, abie in sig_lib_abies.items():
        component_name = abie.get('component_name')
        definition = abie.get('definition', '')
        children = abie.get('children', [])

        if component_name == 'SignatureInformation':
            type_name = component_name + 'Type'
            properties = {}
            required = []

            # $jsonschema for standalone use
            properties['$jsonschema'] = {
                'const': f'{URN_BASE}:SignatureAggregateComponents-2#{type_name}',
                'description': 'Identifies the JSON schema governing this instance.'
            }

            for child in children:
                child_component_name = child['component_name']
                component_type = child.get('component_type')
                cardinality = child.get('cardinality')

                if component_type == 'BBIE':
                    # Reference to SignatureBasicComponents
                    properties[child_component_name] = {
                        '$ref': f'{URN_BASE}:SignatureBasicComponents-2#/$defs/{child_component_name}'
                    }

                # Add to required list if cardinality is 1 or 1..n
                if cardinality in ('1', '1..n'):
                    required.append(child_component_name)

            # Build the ABIE definition
            dictionary_entry_name = abie.get('dictionary_entry_name', '')
            abie_def = {
                '$anchor': type_name,
                'type': 'object',
                'description': definition,
                'properties': properties,
                'additionalProperties': False,
                'minProperties': 1
            }

            if dictionary_entry_name:
                abie_def['title'] = dictionary_entry_name

            if required:
                abie_def['required'] = required

            sig_agg_defs[type_name] = abie_def

    # Build SignatureAggregateComponents schema with sorted $defs
    sig_agg_schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': f'{URN_BASE}:SignatureAggregateComponents-2',
        'description': 'UBL 2.5 Signature Aggregate Components',
        '$defs': dict(sorted(sig_agg_defs.items()))
    }

    # Write SignatureAggregateComponents
    sig_agg_file = output_dir / f'SignatureAggregateComponents{FILE_VERSION_SUFFIX}.json'
    with open(sig_agg_file, 'w') as f:
        json.dump(sig_agg_schema, f, indent=2)
        f.write('\n')

    print(f"  Written SignatureAggregateComponents{FILE_VERSION_SUFFIX}.json")


# ============================================================================
# Step 9: Generate document schemas
# ============================================================================

def generate_document_schemas(output_dir, registry):
    """
    Generate document root schemas (Invoice, Order, etc.).

    Args:
        output_dir: Output directory for schemas
        registry: Built registry from build_registry()

    Generates ~101 document JSON schemas in the output directory.
    Each document has a root ABIE with children (BBIEs and ASBIEs).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Models to skip
    SKIP_MODELS = {
        'UBL-CommonLibrary-2.5',
        'UBL-CommonSignatureComponents-2.5',
        'UBL-SignatureLibrary-2.5',
        'UBL-CommonExtensionComponents-2.5',
    }

    # Build object_class_to_type lookup from CommonLibrary ABIEs
    common_library_abies = registry['models'].get('UBL-CommonLibrary-2.5', {}).get('abies', {})
    object_class_to_type = {}
    for object_class, abie in common_library_abies.items():
        component_name = abie['component_name']
        type_name = component_name + 'Type'
        object_class_to_type[object_class] = type_name

    count = 0

    # Process each document model
    for model_name in sorted(registry['models'].keys()):
        if model_name in SKIP_MODELS:
            continue

        model_data = registry['models'][model_name]
        abies = model_data.get('abies', {})

        # Each document model should have exactly one root ABIE
        if not abies:
            continue

        # Get the root ABIE (typically the first or only one)
        root_abie = None
        root_abie_name = None
        for object_class, abie in abies.items():
            root_abie = abie
            root_abie_name = object_class
            break  # Take the first one as root

        if not root_abie:
            continue

        # Extract document name from model name
        # Pattern: UBL-DocName-2.5 -> DocName
        doc_name = model_name.replace('UBL-', '').replace('-2.5', '')

        # Build the schema
        schema_urn = f"{URN_BASE}:{doc_name}-2"
        definition = root_abie.get('definition', '')
        children = root_abie.get('children', [])

        # Build properties dictionary
        properties = {}
        required = []

        # $jsonschema: identifies this document type (required)
        properties['$jsonschema'] = {
            'const': schema_urn,
            'description': 'Identifies the JSON schema governing this instance.'
        }
        required.append('$jsonschema')

        # 1. Add UBLExtensions (optional)
        properties['UBLExtensions'] = {
            '$ref': f'{URN_BASE}:CommonExtensionComponents-2#/$defs/UBLExtensionsType'
        }

        # 2. Add Signature (optional, 0..n via oneOf)
        properties['Signature'] = {
            'oneOf': [
                {'$ref': f'{URN_BASE}:CommonAggregateComponents-2#/$defs/SignatureType'},
                {
                    'type': 'array',
                    'items': {'$ref': f'{URN_BASE}:CommonAggregateComponents-2#/$defs/SignatureType'}
                }
            ]
        }

        # 3. Add children (BBIEs and ASBIEs)
        for child in children:
            child_component_name = child['component_name']
            component_type = child['component_type']
            cardinality = child['cardinality']

            if component_type == 'BBIE':
                # BBIE: reference to CommonBasicComponents
                ref_schema = {
                    '$ref': f'{URN_BASE}:CommonBasicComponents-2#/$defs/{child_component_name}'
                }

                if cardinality in ('0..1', '1'):
                    properties[child_component_name] = ref_schema
                elif cardinality in ('0..n', '1..n'):
                    # Repeating BBIE: allow single value or array
                    properties[child_component_name] = {
                        'oneOf': [
                            ref_schema,
                            {
                                'type': 'array',
                                'items': ref_schema
                            }
                        ]
                    }
                    if cardinality == '1..n':
                        properties[child_component_name]['oneOf'][1]['minItems'] = 1
                else:
                    properties[child_component_name] = ref_schema

            elif component_type == 'ASBIE':
                # ASBIE: reference to another ABIE (in CommonAggregateComponents)
                associated_object_class = child.get('associated_object_class', '')

                # Resolve the type name
                if associated_object_class in object_class_to_type:
                    target_type = object_class_to_type[associated_object_class]
                else:
                    # Fallback
                    target_type = associated_object_class.replace(' ', '') + 'Type'

                ref_schema = {'$ref': f'{URN_BASE}:CommonAggregateComponents-2#/$defs/{target_type}'}

                if cardinality in ('0..1', '1'):
                    # Single value
                    properties[child_component_name] = ref_schema
                elif cardinality in ('0..n', '1..n'):
                    # Array (single or array)
                    properties[child_component_name] = {
                        'oneOf': [
                            ref_schema,
                            {
                                'type': 'array',
                                'items': ref_schema
                            }
                        ]
                    }
                    # For 1..n, add minItems constraint
                    if cardinality == '1..n':
                        properties[child_component_name]['oneOf'][1]['minItems'] = 1
                else:
                    # Fallback for unknown cardinality
                    properties[child_component_name] = ref_schema

            # Add to required list if cardinality is 1 or 1..n
            if cardinality in ('1', '1..n'):
                required.append(child_component_name)

        # Build the document schema
        dictionary_entry_name = root_abie.get('dictionary_entry_name', '')
        schema = {
            '$schema': 'https://json-schema.org/draft/2020-12/schema',
            '$id': schema_urn,
            'description': definition,
            'type': 'object',
            'properties': properties,
            'required': required,
            'additionalProperties': False,
            'minProperties': 1
        }

        if dictionary_entry_name:
            schema['title'] = dictionary_entry_name

        # Write the schema to file
        filename = f"{doc_name}{FILE_VERSION_SUFFIX}.json"
        output_file = output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(schema, f, indent=2)
            f.write('\n')

        count += 1

    print(f"  Written {count} document schemas")


# ============================================================================
# Step 10: Generate JSON Schema catalog
# ============================================================================

def generate_catalog(output_dir, registry):
    """
    Generate a JSON catalog mapping URNs to schema file paths.

    Args:
        output_dir: Root output directory for schemas (json/schemas/)
        registry: Built registry from build_registry()

    Produces a catalog file that allows schema resolvers to locate
    the actual schema files from their URN-based $id values.
    """
    catalog = {}

    # Common schemas (fixed set)
    common_schemas = [
        'UnqualifiedDataTypes',
        'QualifiedDataTypes',
        'CommonBasicComponents',
        'CommonAggregateComponents',
        'CommonExtensionComponents',
        'SignatureBasicComponents',
        'SignatureAggregateComponents',
    ]
    for name in common_schemas:
        urn = f'{URN_BASE}:{name}-2'
        catalog[urn] = f'common/{name}{FILE_VERSION_SUFFIX}.json'

    # Document schemas
    SKIP_MODELS = {
        'UBL-CommonLibrary-2.5',
        'UBL-CommonSignatureComponents-2.5',
        'UBL-SignatureLibrary-2.5',
        'UBL-CommonExtensionComponents-2.5',
    }

    for model_name in sorted(registry['models'].keys()):
        if model_name in SKIP_MODELS:
            continue

        model_data = registry['models'][model_name]
        if not model_data.get('abies'):
            continue

        doc_name = model_name.replace('UBL-', '').replace('-2.5', '')
        urn = f'{URN_BASE}:{doc_name}-2'
        catalog[urn] = f'maindoc/{doc_name}{FILE_VERSION_SUFFIX}.json'

    # Write the catalog
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_file = output_dir / 'catalog.json'
    with open(catalog_file, 'w') as f:
        json.dump(catalog, f, indent=2)
        f.write('\n')

    print(f"  Written catalog.json ({len(catalog)} entries)")


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Main script flow: parse GC files, build registry, generate schemas."""
    base_dir = Path(__file__).parent
    gc_dir = base_dir / 'gc'
    output_dir = base_dir / 'json' / 'schemas'

    # Step 1: Parse GC files
    print("Step 1: Parsing GC files...")
    main_rows = parse_gc_file(gc_dir / 'UBL-Entities-2.5.gc')
    print(f"  Parsed gc/UBL-Entities-2.5.gc... {len(main_rows)} rows")

    sig_rows = parse_gc_file(gc_dir / 'UBL-Signature-Entities-2.5.gc')
    print(f"  Parsed gc/UBL-Signature-Entities-2.5.gc... {len(sig_rows)} rows")

    ext_rows = parse_gc_file(gc_dir / 'UBL-Extension-Entities-2.5.gc')
    print(f"  Parsed gc/UBL-Extension-Entities-2.5.gc... {len(ext_rows)} rows")

    all_rows = main_rows + sig_rows + ext_rows
    print(f"  Total rows: {len(all_rows)}")

    # Step 2: Build registry
    print("\nStep 2: Building registry...")
    registry = build_registry(all_rows)
    num_models = len(registry['models'])
    num_abies = sum(len(model['abies']) for model in registry['models'].values())
    print(f"  Built registry: {num_models} models, {num_abies} ABIEs")

    # Step 3: Generate UnqualifiedDataTypes
    print(f"\nStep 3: Generating UnqualifiedDataTypes{FILE_VERSION_SUFFIX}.json...")
    generate_unqualified_data_types(output_dir / 'common')

    # Step 4: Generate QualifiedDataTypes
    print(f"\nStep 4: Generating QualifiedDataTypes{FILE_VERSION_SUFFIX}.json...")
    generate_qualified_data_types(output_dir / 'common', all_rows)

    # Step 5: Generate CommonBasicComponents
    print(f"\nStep 5: Generating CommonBasicComponents{FILE_VERSION_SUFFIX}.json...")
    generate_common_basic_components(output_dir / 'common', registry)

    # Step 6: Generate CommonAggregateComponents
    print(f"\nStep 6: Generating CommonAggregateComponents{FILE_VERSION_SUFFIX}.json...")
    generate_common_aggregate_components(output_dir / 'common', registry)

    # Step 7: Generate CommonExtensionComponents
    print(f"\nStep 7: Generating CommonExtensionComponents{FILE_VERSION_SUFFIX}.json...")
    generate_common_extension_components(output_dir / 'common', registry)

    # Step 8: Generate Signature schemas
    print("\nStep 8: Generating Signature schemas...")
    generate_signature_schemas(output_dir / 'common', registry)

    # Step 9: Generate document schemas
    print("\nStep 9: Generating document schemas...")
    generate_document_schemas(output_dir / 'maindoc', registry)

    # Step 10: Generate catalog
    print("\nStep 10: Generating catalog...")
    generate_catalog(output_dir, registry)

    print("\nDone.")


if __name__ == '__main__':
    main()
