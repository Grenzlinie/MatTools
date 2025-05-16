def test_boltzmann(properties):
    import numpy as np
    expected_properties = {
        "Boltzmann_Filling_Distribution": {
            "format": "np.allclose",
            "value": [0.9791034813819097, 0.020459854127734073, 0.00042753972270360594, 8.934091775449048e-06, 1.8669141512139823e-07, 3.901200631921917e-09]
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
        
        # Check type to ensure numerical comparison is possible
        if not isinstance(actual_value, (list, np.ndarray)) or not all(isinstance(x, (int, float)) for x in actual_value):
            errors.append(f"{property_name}: Expected a list or numpy array of numbers but got {type(actual_value)}")
            continue
        
        # Check value or use np.allclose for approximate comparisons
        if expected_format == "np.allclose":
            if not np.allclose(actual_value, expected_value, rtol=1e-3):
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