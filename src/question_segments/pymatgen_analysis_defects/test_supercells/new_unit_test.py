import numpy as np

def test_supercells(properties):
    expected_properties = {
        "supercell_matrix_shape": {
            "format": "tuple",
            "value": (3, 3)
        },
        "matched_supercell_matrix_shape": {
            "format": "tuple",
            "value": (3, 3)
        },
        "supercell_lattice_parameters_consistency": {
            "format": "bool",
            "value": True
        }
    }
    
    errors = []
    
    for property_name, expected_info in expected_properties.items():
        expected_value = expected_info['value']
        expected_format = expected_info['format']
        
        if property_name not in properties:
            errors.append(f"{property_name} not found in input properties")
            continue
        
        actual_value = properties[property_name]
        
        # Check type
        if expected_format == "tuple" and not isinstance(actual_value, tuple):
            errors.append(f"{property_name} is not of type tuple")
            continue
        elif expected_format == "bool" and not isinstance(actual_value, bool):
            errors.append(f"{property_name} is not of type bool")
            continue
        
        # Check value with proper handling of tuples and arrays
        if isinstance(expected_value, tuple):
            if not isinstance(actual_value, tuple) or len(actual_value) != len(expected_value) or any(
                actual != expected for actual, expected in zip(actual_value, expected_value)):
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
        elif isinstance(expected_value, bool):
            if actual_value != expected_value:
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
        else:
            # Handle cases for arrays or other types
            try:
                if np.any(actual_value != expected_value):
                    errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
            except TypeError:
                errors.append(f"{property_name}: Unable to compare {actual_value} with {expected_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"