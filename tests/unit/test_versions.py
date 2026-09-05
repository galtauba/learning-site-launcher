from launcher.git.versions import stable_tags
def test_semver_filters_prereleases_and_sorts():
    assert [tag.name for tag in stable_tags(["v1.9.0","v2.0.0-rc.1","bad","v1.10.0"])] == ["v1.10.0","v1.9.0"]
