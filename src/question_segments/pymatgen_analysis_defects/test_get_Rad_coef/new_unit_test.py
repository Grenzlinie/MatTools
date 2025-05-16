def test_get_Rad_coef(properties):
    import numpy as np
    expected_properties = {
        "Radiative_Coefficient": {
            "format": "np.allclose",
            "value": [6.97397183e-31, 6.98245178e-31, 7.38666936e-31]
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
        
        # Check value using np.allclose for approximate comparisons
        if expected_format == "np.allclose":
            if not isinstance(actual_value, (np.ndarray, list)):
                errors.append(f"{property_name}: Actual value must be an array-like type for np.allclose, got {type(actual_value)}")
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