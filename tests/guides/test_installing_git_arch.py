#!/usr/bin/env python3
"""
Test suite for Arch Linux Git installation and configuration guide.
Verifies git version availability, global user configuration, credential helper,
and commit author metadata inheritance in an isolated environment.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest


class TestInstallingGitArch(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="git_arch_test_")
        self.fake_home = os.path.join(self.test_dir, "home")
        os.makedirs(self.fake_home, exist_ok=True)
        self.global_config = os.path.join(self.fake_home, ".gitconfig")

        self.env = os.environ.copy()
        self.env["HOME"] = self.fake_home
        self.env["GIT_CONFIG_GLOBAL"] = self.global_config
        # Strip author/committer overrides so git must rely on gitconfig
        for var in ["GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"]:
            self.env.pop(var, None)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def run_cmd(self, cmd, cwd=None, check=True):
        res = subprocess.run(
            cmd,
            cwd=cwd or self.test_dir,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if check and res.returncode != 0:
            raise RuntimeError(f"Command {' '.join(cmd)} failed ({res.returncode}): {res.stderr}")
        return res

    def test_git_version(self):
        """Verifies `git --version` output."""
        res = self.run_cmd(["git", "--version"])
        self.assertEqual(res.returncode, 0)
        self.assertRegex(res.stdout, r"git version \d+\.\d+")

    def test_git_config_and_commit_attribution(self):
        """Verifies git config --global user.name, user.email, and commit metadata."""
        target_name = "Course Student"
        target_email = "student@example.invalid"

        # Set user name and email
        self.run_cmd(["git", "config", "--global", "user.name", target_name])
        self.run_cmd(["git", "config", "--global", "user.email", target_email])

        # Verify git config list
        list_res = self.run_cmd(["git", "config", "--list"])
        self.assertIn(f"user.name={target_name}", list_res.stdout)
        self.assertIn(f"user.email={target_email}", list_res.stdout)

        # Initialize temporary repository
        repo_dir = os.path.join(self.test_dir, "repo")
        os.makedirs(repo_dir)
        self.run_cmd(["git", "init", "-b", "main"], cwd=repo_dir)

        # Create a test commit
        with open(os.path.join(repo_dir, "notes.txt"), "w") as f:
            f.write("alpha\n")
        self.run_cmd(["git", "add", "notes.txt"], cwd=repo_dir)
        self.run_cmd(["git", "commit", "-m", "Commit A"], cwd=repo_dir)

        # Assert commit embeds the configured user.name and user.email
        log_res = self.run_cmd(["git", "log", "-1", "--format=%an <%ae>"], cwd=repo_dir)
        self.assertEqual(log_res.stdout.strip(), f"{target_name} <{target_email}>")

    def test_credential_helper_config(self):
        """Verifies credential helper configuration."""
        self.run_cmd(["git", "config", "--global", "credential.helper", "cache"])
        get_res = self.run_cmd(["git", "config", "--global", "credential.helper"])
        self.assertEqual(get_res.stdout.strip(), "cache")


if __name__ == "__main__":
    unittest.main()
