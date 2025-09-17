"""Module for comparing YAML structures and generating diff output."""

from typing import Any, Dict, List, Set, Tuple

from deepdiff import DeepDiff


class YamlComparer:
    """Compares YAML structures and generates detailed diff reports."""

    def compare(self, taqasta_yaml: Dict[str, Any], canasta_yaml: Dict[str, Any],
                taqasta_ref: str, canasta_ref: str, mw_version: str = None) -> str:
        """Compare two YAML structures and return a formatted diff."""
        output = []
        output.append(f"Comparing Taqasta ({taqasta_ref}) vs Canasta ({canasta_ref})")
        if mw_version:
            output.append(f"MediaWiki Version: {mw_version}")
        output.append("=" * 70)

        # Compare extensions
        ext_diff = self._compare_extensions(
            taqasta_yaml.get('extensions', []),
            canasta_yaml.get('extensions', [])
        )
        if ext_diff:
            output.append("\nEXTENSIONS:")
            output.append(ext_diff)

        # Compare skins
        skin_diff = self._compare_skins(
            taqasta_yaml.get('skins', []),
            canasta_yaml.get('skins', [])
        )
        if skin_diff:
            output.append("\nSKINS:")
            output.append(skin_diff)

        # Compare packages
        pkg_diff = self._compare_packages(
            taqasta_yaml.get('packages', []),
            canasta_yaml.get('extensions', [])
        )
        if pkg_diff:
            output.append("\nCOMPOSER PACKAGES:")
            output.append(pkg_diff)

        # Compare repositories
        repo_diff = self._compare_repositories(
            taqasta_yaml.get('repositories', []),
            canasta_yaml
        )
        if repo_diff:
            output.append("\nREPOSITORIES:")
            output.append(repo_diff)

        if not any([ext_diff, skin_diff, pkg_diff, repo_diff]):
            output.append("\nNo differences found!")

        return "\n".join(output)

    def _compare_extensions(self, taqasta_exts: List[Dict[str, Any]],
                           canasta_exts: List[Dict[str, Any]]) -> str:
        """Compare extensions between Taqasta and Canasta."""
        output = []

        # Convert both lists to dicts for easier comparison
        taqasta_ext_dict = {ext: data for item in taqasta_exts
                           for ext, data in item.items()}
        canasta_ext_dict = {ext: data for item in canasta_exts
                           for ext, data in item.items()}

        taqasta_names = set(taqasta_ext_dict.keys())
        canasta_names = set(canasta_ext_dict.keys())

        # Extensions only in Taqasta
        only_taqasta = taqasta_names - canasta_names
        if only_taqasta:
            output.append("  Extensions only in Taqasta:")
            for ext in sorted(only_taqasta):
                output.append(f"    + {ext}")
                # Show key details
                ext_data = taqasta_ext_dict[ext]
                if 'commit' in ext_data:
                    output.append(f"        commit: {ext_data['commit']}")
                if 'repository' in ext_data:
                    output.append(f"        repository: {ext_data['repository']}")

        # Extensions only in Canasta
        only_canasta = canasta_names - taqasta_names
        if only_canasta:
            output.append("  Extensions only in Canasta:")
            for ext in sorted(only_canasta):
                output.append(f"    - {ext}")
                # Show key details
                ext_data = canasta_ext_dict[ext]
                if 'commit' in ext_data:
                    output.append(f"        commit: {ext_data['commit']}")
                if 'repository' in ext_data:
                    output.append(f"        repository: {ext_data['repository']}")

        # Extensions in both - compare details
        common = taqasta_names & canasta_names
        if common:
            differences = []
            for ext in sorted(common):
                taqasta_data = taqasta_ext_dict[ext]
                canasta_data = canasta_ext_dict[ext]

                diff = DeepDiff(taqasta_data, canasta_data, ignore_order=True)
                if diff:
                    differences.append((ext, taqasta_data, canasta_data, diff))

            if differences:
                output.append("  Extensions with different configurations:")
                for ext, taqasta_data, canasta_data, diff in differences:
                    output.append(f"    ~ {ext}:")

                    # Compare commits
                    taqasta_commit = taqasta_data.get('commit')
                    canasta_commit = canasta_data.get('commit')
                    if taqasta_commit != canasta_commit:
                        output.append(f"        Taqasta commit: {taqasta_commit}")
                        output.append(f"        Canasta commit: {canasta_commit}")

                    # Compare repositories
                    taqasta_repo = taqasta_data.get('repository')
                    canasta_repo = canasta_data.get('repository')
                    if taqasta_repo != canasta_repo:
                        output.append(f"        Taqasta repo: {taqasta_repo or 'wikimedia'}")
                        output.append(f"        Canasta repo: {canasta_repo or 'wikimedia'}")

                    # Compare branches
                    taqasta_branch = taqasta_data.get('branch')
                    canasta_branch = canasta_data.get('branch')
                    if taqasta_branch != canasta_branch:
                        output.append(f"        Taqasta branch: {taqasta_branch or 'REL1_43'}")
                        output.append(f"        Canasta branch: {canasta_branch or 'REL1_43'}")

                    # Compare additional steps
                    taqasta_steps = set(taqasta_data.get('additional steps', []))
                    canasta_steps = set(canasta_data.get('additional steps', []))
                    if taqasta_steps != canasta_steps:
                        only_taqasta_steps = taqasta_steps - canasta_steps
                        only_canasta_steps = canasta_steps - taqasta_steps
                        if only_taqasta_steps:
                            output.append(f"        Only in Taqasta: {list(only_taqasta_steps)}")
                        if only_canasta_steps:
                            output.append(f"        Only in Canasta: {list(only_canasta_steps)}")

                    # Show any other differences detected by DeepDiff
                    if not any([
                        taqasta_commit != canasta_commit,
                        taqasta_repo != canasta_repo,
                        taqasta_branch != canasta_branch,
                        taqasta_steps != canasta_steps
                    ]):
                        # If no specific differences were shown, display the actual DeepDiff details
                        output.append(f"        Other differences:")
                        for change_type, changes in diff.items():
                            if change_type == 'values_changed':
                                for path, change in changes.items():
                                    old_val = change.get('old_value', 'None')
                                    new_val = change.get('new_value', 'None')
                                    output.append(f"          {path}: '{old_val}' → '{new_val}'")
                            elif change_type == 'type_changes':
                                for path, change in changes.items():
                                    old_type = change.get('old_type', 'Unknown')
                                    new_type = change.get('new_type', 'Unknown')
                                    output.append(f"          {path}: type changed from {old_type} to {new_type}")
                            elif change_type == 'dictionary_item_added':
                                for path in changes:
                                    output.append(f"          Added: {path}")
                            elif change_type == 'dictionary_item_removed':
                                for path in changes:
                                    output.append(f"          Removed: {path}")
                            elif change_type == 'iterable_item_added':
                                output.append(f"          Added {len(changes)} item(s) to iterable")
                            elif change_type == 'iterable_item_removed':
                                output.append(f"          Removed {len(changes)} item(s) from iterable")

        return "\n".join(output) if output else ""

    def _compare_skins(self, taqasta_skins: List[Dict[str, Any]],
                      canasta_skins: List[Dict[str, Any]]) -> str:
        """Compare skins between Taqasta and Canasta."""
        output = []

        # Convert both lists to dicts
        taqasta_skin_dict = {skin: data for item in taqasta_skins
                            for skin, data in item.items()}
        canasta_skin_dict = {skin: data for item in canasta_skins
                            for skin, data in item.items()}

        taqasta_names = set(taqasta_skin_dict.keys())
        canasta_names = set(canasta_skin_dict.keys())

        # Skins only in Taqasta
        only_taqasta = taqasta_names - canasta_names
        if only_taqasta:
            output.append("  Skins only in Taqasta:")
            for skin in sorted(only_taqasta):
                output.append(f"    + {skin}")

        # Skins only in Canasta
        only_canasta = canasta_names - taqasta_names
        if only_canasta:
            output.append("  Skins only in Canasta:")
            for skin in sorted(only_canasta):
                output.append(f"    - {skin}")

        # Skins in both - compare details
        common = taqasta_names & canasta_names
        if common:
            differences = []
            for skin in sorted(common):
                taqasta_data = taqasta_skin_dict[skin]
                canasta_data = canasta_skin_dict[skin]

                diff = DeepDiff(taqasta_data, canasta_data, ignore_order=True)
                if diff:
                    differences.append((skin, taqasta_data, canasta_data, diff))

            if differences:
                output.append("  Skins with different configurations:")
                for skin, taqasta_data, canasta_data, diff in differences:
                    output.append(f"    ~ {skin}:")

                    # Compare commits
                    taqasta_commit = taqasta_data.get('commit')
                    canasta_commit = canasta_data.get('commit')
                    if taqasta_commit != canasta_commit:
                        output.append(f"        Taqasta commit: {taqasta_commit}")
                        output.append(f"        Canasta commit: {canasta_commit}")

                    # Show any other differences detected by DeepDiff
                    if taqasta_commit == canasta_commit:
                        # If no specific differences were shown, display the actual DeepDiff details
                        output.append(f"        Other differences:")
                        for change_type, changes in diff.items():
                            if change_type == 'values_changed':
                                for path, change in changes.items():
                                    old_val = change.get('old_value', 'None')
                                    new_val = change.get('new_value', 'None')
                                    output.append(f"          {path}: '{old_val}' → '{new_val}'")
                            elif change_type == 'type_changes':
                                for path, change in changes.items():
                                    old_type = change.get('old_type', 'Unknown')
                                    new_type = change.get('new_type', 'Unknown')
                                    output.append(f"          {path}: type changed from {old_type} to {new_type}")
                            elif change_type == 'dictionary_item_added':
                                for path in changes:
                                    output.append(f"          Added: {path}")
                            elif change_type == 'dictionary_item_removed':
                                for path in changes:
                                    output.append(f"          Removed: {path}")
                            elif change_type == 'iterable_item_added':
                                output.append(f"          Added {len(changes)} item(s) to iterable")
                            elif change_type == 'iterable_item_removed':
                                output.append(f"          Removed {len(changes)} item(s) from iterable")

        return "\n".join(output) if output else ""

    def _compare_packages(self, taqasta_packages: List[Dict[str, str]],
                         canasta_exts: List[Dict[str, Any]]) -> str:
        """Compare composer packages between Taqasta and Canasta."""
        output = []

        # Extract package names from Canasta extensions that have composer packages
        canasta_packages = set()
        for ext_item in canasta_exts:
            for ext_name, ext_data in ext_item.items():
                if ext_data.get('additional steps') and 'composer update' in ext_data['additional steps']:
                    canasta_packages.add(ext_name.lower())

        taqasta_package_names = set()
        for pkg in taqasta_packages:
            if 'name' in pkg:
                taqasta_package_names.add(pkg['name'].lower())

        # Packages only in Taqasta
        only_taqasta = taqasta_package_names - canasta_packages
        if only_taqasta:
            output.append("  Composer packages only in Taqasta:")
            for pkg in sorted(only_taqasta):
                # Find the full package info
                for tp in taqasta_packages:
                    if tp.get('name', '').lower() == pkg:
                        version = tp.get('version', 'dev')
                        output.append(f"    + {tp['name']} @ {version}")
                        break

        # Packages only in Canasta (extensions that need composer update)
        only_canasta = canasta_packages - taqasta_package_names
        if only_canasta:
            output.append("  Extensions requiring composer update only in Canasta:")
            for ext in sorted(only_canasta):
                output.append(f"    - {ext}")

        return "\n".join(output) if output else ""

    def _compare_repositories(self, taqasta_repos: List[Dict[str, str]],
                             canasta_yaml: Dict[str, Any]) -> str:
        """Compare custom repositories."""
        output = []

        # Taqasta repositories
        taqasta_repo_urls = set()
        for repo in taqasta_repos:
            if 'url' in repo:
                taqasta_repo_urls.add(repo['url'])

        # Canasta doesn't have explicit repositories section, but extensions may reference repos
        canasta_repo_urls = set()
        for section in ['extensions', 'skins']:
            if section in canasta_yaml:
                for item in canasta_yaml[section]:
                    for name, data in item.items():
                        if 'repository' in data:
                            canasta_repo_urls.add(data['repository'])

        # Compare
        only_taqasta = taqasta_repo_urls - canasta_repo_urls
        only_canasta = canasta_repo_urls - taqasta_repo_urls

        if only_taqasta:
            output.append("  Custom repositories only in Taqasta:")
            for repo in sorted(only_taqasta):
                output.append(f"    + {repo}")

        if only_canasta:
            output.append("  Custom repositories only in Canasta:")
            for repo in sorted(only_canasta):
                output.append(f"    - {repo}")

        return "\n".join(output) if output else ""
