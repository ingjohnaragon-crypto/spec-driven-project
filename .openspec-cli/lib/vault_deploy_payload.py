#!/usr/bin/env python3
"""
vault_deploy_payload.py — v6
Builds the JSON payload for POST /v1/product-versions
Usage: python3 vault_deploy_payload.py <contract_file> <product_id> <display_name> <api_version>

Cambios v6 (confirmado contra documentacion oficial de contracts_api):
- INSTANCE-level parameters: NO necesitan entrada en params[] del deploy.
  Su update_permission debe estar declarado en el PROPIO CODIGO del
  contrato (Parameter(level=ParameterLevel.INSTANCE, update_permission=...)).
  Su default_value en codigo solo aplica a migraciones de cuenta, no a
  deploy ni a creacion de cuenta nueva.
- TEMPLATE/GLOBAL-level parameters: SI necesitan una entrada en params[]
  con "value" (no "default_value") -- son valores fijos a nivel de
  producto que deben fijarse en el momento del deploy.
"""
import ast
import json
import re
import sys
import uuid

contract_file = sys.argv[1]
product_id    = sys.argv[2]
display_name  = sys.argv[3]
api_version   = sys.argv[4] if len(sys.argv) > 4 else "3.11.0"

with open(contract_file, encoding="utf-8") as f:
    code = f.read()


def extract_supported_denominations(source: str) -> list:
    patterns = (
        r"supported_denominations\s*=\s*(\[[^\]]+\])",
    )
    for pattern in patterns:
        match = re.search(pattern, source)
        if not match:
            continue
        try:
            value = ast.literal_eval(match.group(1))
        except (SyntaxError, ValueError):
            continue
        if isinstance(value, list) and value and all(isinstance(item, str) for item in value):
            return value
    return ["GBP"]


def _literal_value(node):
    if isinstance(node, ast.Call):
        func_name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if func_name == "Decimal" and node.args:
            inner = node.args[0]
            if isinstance(inner, ast.Constant):
                return str(inner.value)
            return None
        if func_name == "OptionalValue" and node.args:
            # OptionalValue(UnionItemValue("false")) -> extraer el key interno
            return _literal_value(node.args[0])
        if func_name == "UnionItemValue" and node.args:
            inner = node.args[0]
            if isinstance(inner, ast.Constant):
                return str(inner.value)
            return None
        return None
    if isinstance(node, ast.Constant):
        return str(node.value)
    return None


def extract_template_params(source: str) -> list:
    """Solo parametros TEMPLATE/GLOBAL necesitan 'value' en el deploy."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    params_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "parameters":
                    params_node = node.value
                    break
        if params_node is not None:
            break

    if params_node is None or not isinstance(params_node, ast.List):
        return []

    result = []
    for element in params_node.elts:
        if not isinstance(element, ast.Call):
            continue
        kwargs = {kw.arg: kw.value for kw in element.keywords}

        name_node = kwargs.get("name")
        name = _literal_value(name_node) if name_node else None
        if not name:
            continue

        level_node = kwargs.get("level")
        level_str = None
        if isinstance(level_node, ast.Attribute):
            level_str = level_node.attr

        if level_str not in ("TEMPLATE", "GLOBAL"):
            continue  # INSTANCE no necesita entrada aqui

        default_node = kwargs.get("default_value")
        value = _literal_value(default_node) if default_node else None
        if value is None:
            continue  # sin valor conocido, no lo mandamos (evita mandar "")

        result.append({
            "name": name,
            "value": value,
        })

    return result


payload = {
    "request_id": str(uuid.uuid4()),
    "product_version": {
        "product_id":      product_id,
        "display_name":    display_name,
        "code":            code,
        "contracts_language_api_version": {
            "major": int(api_version.split(".")[0]),
            "minor": int(api_version.split(".")[1]),
            "patch": int(api_version.split(".")[2])
        },
        "params":          extract_template_params(code),
        "supported_denominations": extract_supported_denominations(code),
        "is_current":      True
    }
}

print(json.dumps(payload, indent=2))
