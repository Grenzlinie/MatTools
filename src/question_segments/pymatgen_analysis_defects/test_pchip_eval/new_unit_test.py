def test_pchip_eval(properties):
    import numpy as np
    expected_properties = {
        "pchip_interpolation_integral": {
            "format": "np.allclose",
            "value": "8.227688936841835"
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
            if not isinstance(actual_value, (float, int)):
                errors.append(f"{property_name} is not of type float or int")
                continue
            
            expected_value = float(expected_value)  # Convert expected_value to float for comparison
            
            # Check value using np.allclose for approximate comparisons
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