def test_vacancy(properties):
    import numpy as np
    from pymatgen.core.periodic_table import Element
    
    expected_properties = {
        "symmetry_equivalence": {
            "format": "bool",
            "value": True
        },
        "vacancy_string_representation": {
            "format": "str",
            "value": "Ga Vacancy defect at site #0"
        },
        "vacancy_oxidation_state": {
            "format": "int",
            "value": -3
        },
        "vacancy_charge_states": {
            "format": "list",
            "value": [-4, -3, -2, -1, 0, 1]
        },
        "vacancy_multiplicity": {
            "format": "int",
            "value": 2
        },
        "vacancy_supercell_formula": {
            "format": "str",
            "value": "Ga63 N64"
        },
        "vacancy_name": {
            "format": "str",
            "value": "v_Ga"
        },
        "vacancy_self_equivalence": {
            "format": "bool",
            "value": True
        },
        "vacancy_element_changes": {
            "format": "dict",
            "value": {Element('Ga'): -1}
        },
        "vacancy_latex_name": {
            "format": "str",
            "value": "v$_{\\rm Ga}$"
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