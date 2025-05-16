def test_get_vibronic_matrix_elements(properties):
    import numpy as np
    expected_properties = {
        "vibronic_matrix_elements": {
            "format": "np.allclose",
            "value": [0.0, 3984589.0407885523, 0.0, 0.0, 0.0]
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
        
        # Check value type before using np.allclose for approximate comparisons
        if expected_format == "np.allclose":
            if not isinstance(actual_value, (list, np.ndarray)):
                errors.append(f"{property_name}: Actual value type {type(actual_value)} is not suitable for np.allclose")
            elif not np.allclose(actual_value, expected_value):
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