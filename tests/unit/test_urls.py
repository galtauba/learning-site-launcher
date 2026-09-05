from launcher.github.urls import github_owner_repo, github_web_url
def test_https_and_ssh_urls():
    assert github_owner_repo("https://github.com/owner/repo.git") == ("owner","repo")
    assert github_owner_repo("git@github.com:owner/repo.git") == ("owner","repo")
    assert github_web_url("git@github.com:owner/repo.git") == "https://github.com/owner/repo"
def test_reject_non_github(): assert github_owner_repo("https://example.com/x/y") is None
