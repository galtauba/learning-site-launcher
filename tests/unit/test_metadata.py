import json
from launcher.projects.metadata import load_metadata
def test_metadata_defaults_and_extension(tmp_path):
    assert load_metadata(tmp_path)["editorEntry"] == "main.py"
    (tmp_path/".learning-site.json").write_text(json.dumps({"siteVersion":"1.2.0","newField":True}))
    assert load_metadata(tmp_path)["siteVersion"] == "1.2.0"
