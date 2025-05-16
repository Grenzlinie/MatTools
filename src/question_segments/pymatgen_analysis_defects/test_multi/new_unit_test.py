def test_multi(properties):
    import numpy as np
    expected_properties = {
        "Fermi_Level_Solution": {
            "format": "float",
            "value": "ef > 0"
        },
        "Formation_Energy_Diagrams_Count": {
            "format": "int",
            "value": 1
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
        
        # Check type (skip type check for np.allclose cases as it's handled separately)
        if expected_format != "np.allclose" and not isinstance(actual_value, eval(expected_format)):
            errors.append(f"{property_name} is not of type {expected_format}")
            continue
        
        # Check value or use np.allclose for approximate comparisons
        if property_name == "Fermi_Level_Solution":
            # Special case for Fermi_Level_Solution to check if ef > 0
            if not (isinstance(actual_value, float) and actual_value > 0):
                errors.append(f"{property_name}: Expected a float greater than 0 but got {actual_value}")
        else:
            if actual_value != expected_value:
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"