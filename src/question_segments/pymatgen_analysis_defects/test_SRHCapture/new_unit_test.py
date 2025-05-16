def test_SRHCapture(properties):
    import numpy as np
    
    expected_properties = {
        "SRH_Coefficient": {
            "format": "np.allclose",
            "value": [1.89187260e-34, 6.21019152e-33, 3.51501688e-31]
        },
        "RuntimeError_Check": {
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
        
        # Check type for np.allclose requirements
        if expected_format == "np.allclose":
            # Ensure actual_value is convertible to a NumPy array
            try:
                actual_value = np.array(actual_value, dtype=np.float64)
                expected_value = np.array(expected_value, dtype=np.float64)
            except (ValueError, TypeError):
                errors.append(f"{property_name} contains non-numeric data or incompatible types")
                continue
            
            # Check value using np.allclose for approximate comparisons
            if not np.allclose(actual_value, expected_value):
                errors.append(f"{property_name}: Expected value close to {expected_value.tolist()} but got {actual_value.tolist()}")
        else:
            # Check type for other formats
            if not isinstance(actual_value, eval(expected_format)):
                errors.append(f"{property_name} is not of type {expected_format}")
                continue
            
            # Check value
            if actual_value != expected_value:
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"