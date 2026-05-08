"""Agent factory functions."""

from codemonkeys.agents.architecture_reviewer import make_architecture_reviewer
from codemonkeys.agents.changelog_reviewer import make_changelog_reviewer
from codemonkeys.agents.fixer import make_fixer
from codemonkeys.agents.python_characterization_tester import (
    make_python_characterization_tester,
)
from codemonkeys.agents.python_file_reviewer import make_python_file_reviewer
from codemonkeys.agents.python_implementer import make_python_implementer
from codemonkeys.agents.python_structural_refactorer import (
    make_python_structural_refactorer,
)
from codemonkeys.agents.readme_reviewer import make_readme_reviewer
from codemonkeys.agents.review_auditor import make_review_auditor
from codemonkeys.agents.spec_compliance_reviewer import make_spec_compliance_reviewer

__all__ = [
    "make_architecture_reviewer",
    "make_changelog_reviewer",
    "make_fixer",
    "make_python_characterization_tester",
    "make_python_file_reviewer",
    "make_python_implementer",
    "make_python_structural_refactorer",
    "make_readme_reviewer",
    "make_review_auditor",
    "make_spec_compliance_reviewer",
]
