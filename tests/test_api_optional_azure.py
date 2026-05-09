"""
Regression tests for optional provider dependency isolation.

These tests verify the structural isolation of optional dependencies:
- Azure SDK is only imported inside endpoint handler functions, not at module level.
- boto3/botocore are only imported inside the classes that need them (lazy), not at module level.
- The API router registers Azure routes through a helper that catches ModuleNotFoundError.
"""
# pylint: disable=E0401

import ast
import inspect
import textwrap

import app.api.api_v1.api as api_mod
import app.api.api_v1.endpoints.detect_person_azure as detect_azure_mod
import app.api.api_v1.endpoints.register_face_azure as register_azure_mod
import app.api.api_v1.endpoints.upload_face_azure as upload_azure_mod
import app.api.api_v1.endpoints.delete_face_azure as delete_azure_mod
import app.api.api_v1.endpoints.list_faces_azure as list_azure_mod
import app.api.api_v1.endpoints.detect_person as detect_person_mod
import app.api.api_v1.endpoints.register_face as register_face_mod
import app.api.api_v1.endpoints.train_face as train_face_mod
import app.api.api_v1.endpoints.upload_face as upload_face_mod
import app.api.api_v1.endpoints.delete_face as delete_face_mod
import app.api.api_v1.endpoints.list_faces as list_faces_mod
import app.classes.adapters.config_aws as config_aws_mod
import app.classes.adapters.storage_s3_aws as storage_mod


# ── helpers ───────────────────────────────────────────────────────────────────

def _top_level_imports(module):
    """Return set of top-level module names imported at module level (not inside functions)."""
    source = inspect.getsource(module)
    tree = ast.parse(textwrap.dedent(source))
    names = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split('.')[0])
            else:
                if node.module:
                    names.add(node.module.split('.')[0])
    return names


# ── Azure endpoints: azure must NOT appear at module level ────────────────────

def test_detect_person_azure_no_azure_at_module_level():
    assert 'azure' not in _top_level_imports(detect_azure_mod)

def test_register_face_azure_no_azure_at_module_level():
    assert 'azure' not in _top_level_imports(register_azure_mod)

def test_upload_face_azure_no_azure_at_module_level():
    assert 'azure' not in _top_level_imports(upload_azure_mod)

def test_delete_face_azure_no_azure_at_module_level():
    assert 'azure' not in _top_level_imports(delete_azure_mod)

def test_list_faces_azure_no_azure_at_module_level():
    assert 'azure' not in _top_level_imports(list_azure_mod)


# ── Rekognition endpoints: boto3 must NOT appear at module level ─────────────

def test_detect_person_no_boto3_at_module_level():
    assert 'boto3' not in _top_level_imports(detect_person_mod)

def test_register_face_no_boto3_at_module_level():
    assert 'boto3' not in _top_level_imports(register_face_mod)

def test_train_face_no_boto3_at_module_level():
    assert 'boto3' not in _top_level_imports(train_face_mod)

def test_upload_face_no_boto3_at_module_level():
    assert 'boto3' not in _top_level_imports(upload_face_mod)

def test_delete_face_no_boto3_at_module_level():
    assert 'boto3' not in _top_level_imports(delete_face_mod)

def test_list_faces_no_boto3_at_module_level():
    assert 'boto3' not in _top_level_imports(list_faces_mod)


# ── Infrastructure adapters: boto3 must NOT appear at module level ────────────

def test_config_aws_no_boto3_at_module_level():
    assert 'boto3' not in _top_level_imports(config_aws_mod)

def test_storage_s3_no_boto3_at_module_level():
    assert 'boto3' not in _top_level_imports(storage_mod)


# ── api.py: Azure routers are wrapped in a try/except helper ─────────────────

def test_api_azure_routes_registered_via_optional_helper():
    """_include_azure_routers must exist and catch ModuleNotFoundError."""
    assert hasattr(api_mod, '_include_azure_routers'), \
        "_include_azure_routers helper missing from api.py"
    source = inspect.getsource(api_mod._include_azure_routers)
    assert 'ModuleNotFoundError' in source