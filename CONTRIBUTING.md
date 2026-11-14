# Contributing

Use Windows and Python 3.12. The supported release source is the complete package
produced by Build-Release.ps1; historical Level 1/2 and local state are excluded.

Run `python -m unittest discover -s scripts -p "test_*.py"`, then
`python scripts/validate_publication.py` and `./Build-Release.ps1` before opening a
pull request. Tests must use temporary configuration and mock cloud services;
never use real API Keys, microphones or personal chats in automated checks.

Preserve plugin identity, native settings, original chat permissions, AGPLv3 and
third-party notices. Do not modify model integrity hashes without verifying the
source revision and affected files. Describe behavior changes and checks in the PR.

Free, open-source, ad-free forks for learning, education and community use are welcome. The maintainer discourages paid access, advertising and other commercial monetization of this fan project. The project's original code remains governed by AGPL-3.0-only. Follow its corresponding-source requirements when distributing a modified version or making it available for users to interact with over a network. Third-party materials remain subject to their own terms.

Contributions are accepted under AGPL-3.0-only. Keep upstream copyright and
licensing for third-party content. Report vulnerabilities as described in SECURITY.md.

The builder generates package-files.json for persistent installation integrity.
Publish the generated, reviewed source tree rather than copying local config or
environments into the repository. The root marketplace points to the complete
package, including its setup skill and scripts.
