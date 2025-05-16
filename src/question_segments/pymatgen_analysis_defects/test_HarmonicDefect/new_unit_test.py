def test_HarmonicDefect(properties):
    import numpy as np
    expected_properties = {
        "defect_band_initial": {
            "format": "list of tuples",
            "value": [(138, 0, 1), (138, 1, 1)]
        },
        "defect_band_from_directories": {
            "format": "list of tuples",
            "value": [(138, 0, 1), (138, 1, 1)]
        },
        "spin_index": {
            "format": "int",
            "value": 1
        },
        "non_unique_spin_error": {
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
        
        # Check type for list of tuples
        if expected_format == "list of tuples":
            if not isinstance(actual_value, list) or not all(isinstance(i, tuple) for i in actual_value):
                errors.append(f"{property_name} is not of type {expected_format}")
                continue
            # Compare each tuple in the list
            if len(actual_value) != len(expected_value) or any(a != b for a, b in zip(actual_value, expected_value)):
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
        elif expected_format != "np.allclose" and not isinstance(actual_value, eval(expected_format)):
            errors.append(f"{property_name} is not of type {expected_format}")
            continue
        
        # Check value or use np.allclose for approximate comparisons
        if expected_format == "np.allclose":
            if not np.allclose(actual_value, expected_value):
                errors.append(f"{property_name}: Expected value close to {expected_value} but got {actual_value}")
        else:
            if actual_value != expected_value:
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"