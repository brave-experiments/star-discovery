Changelog
===

0.2.3
---

Disable debug checks when running tests.


0.2.2
---

Add a `--debug` commandline argument, so that `asserts` and other internal
validation checks can be disabled for normal use. This works around the
problem of there being no way to pass `-O` (or otherwise run a pyproject.toml
built script in python's "optimized" mode).

0.2.1
---

Restructure classes so that recovery nodes do not hold a reference to
`BeautifulSoup` `Tag` instances, and now dynamically re-pull them out of the
`BeautifulSoup` document after being unpickled. This worked around an issue in
`BeautifulSoup` where multiple objects holding references to different parts
of a `BeautifulSoup` document could trigger a recursion limit error when
pickling.

Also work around an bug in `BeautifulSoup` where documents would loose a text
node when being unpickled.

Fix an issue where documents with html comments would cause validation errors,
due to `star-discovery` incorrectly calling `NavigableString.output_ready()`.

0.2.0
---

Correctly handle all attributes that have either a single or multiple attributes,
based on the `BeautifulSoup` parser's determination.

Added initial `pytest` integration.
