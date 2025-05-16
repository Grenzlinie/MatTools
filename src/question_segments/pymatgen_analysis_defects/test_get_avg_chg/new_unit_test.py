def test_get_avg_chg(properties):
    import numpy as np
    expected_properties = {
        "average_charge_density": {
            "format": "np.allclose",
            "value": 0.021302511375915358
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
        
        # Check type before using np.allclose
        if expected_format == "np.allclose":
            if not isinstance(actual_value, float):
                errors.append(f"{property_name} is not of type float")
                continue
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