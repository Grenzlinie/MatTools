def test_defect_finder(properties):
    import numpy as np
    expected_properties = {
        "vacancy_defect_distance": {
            "format": "float",
            "value": 0.5
        },
        "interstitial_defect_distance": {
            "format": "float",
            "value": 0.5
        },
        "anti_site_initial_distance": {
            "format": "float",
            "value": 2.0
        },
        "anti_site_defect_distance": {
            "format": "float",
            "value": 0.5
        }
    }
    
    errors = []

    for property_name, expected_info in expected_properties.items():  # Changed expected_value to expected_info
        if property_name not in properties:
            errors.append(f"{property_name} not found in input properties")
            continue
        
        actual_value = properties[property_name]
        
        # Check if actual value is equal to expected value
        if not isinstance(actual_value, (float, int)):
            errors.append(f"{property_name} should be a numeric type")
            continue
        
        if actual_value != expected_info['value']:
            errors.append(f"{property_name}: Expected equal to {expected_info['value']}, but got {actual_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"