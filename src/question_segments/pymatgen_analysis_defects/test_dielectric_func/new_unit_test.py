def test_dielectric_func(properties):
    import numpy as np
    expected_properties = {
        "inter_vbm_integral": {
            "format": "np.allclose",
            "value": 6.31
        },
        "inter_cbm_integral": {
            "format": "np.allclose",
            "value": 0.27
        },
        "optical_transitions_dataframe_type": {
            "format": "bool",
            "value": True
        },
        "optical_transitions_dataframe_length": {
            "format": "int",
            "value": 11
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
        
        # Check type before numerical comparison
        if expected_format == "np.allclose":
            if not isinstance(actual_value, (float, int)):
                errors.append(f"{property_name} is not of type float, int, or np.ndarray")
                continue
        else:
            if not isinstance(actual_value, eval(expected_format)):
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