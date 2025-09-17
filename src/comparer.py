"""Module for comparing YAML structures and generating diff output."""

from typing import Any, Dict, List, Set, Tuple

from deepdiff import DeepDiff


class YamlComparer:
    """Compares YAML structures and generates detailed diff reports."""

    def _clean_diff_path(self, path: str) -> str:
        """Clean up DeepDiff path to be more user-friendly."""
        # Remove "root" prefix and clean up the path
        if path.startswith("root"):
            # Handle cases like root['field'][1] -> field[1] or root["field"][1] -> field[1]
            if (path.startswith("root['") and "']" in path) or (path.startswith('root["') and '"]' in path):
                # Find the first "']" or '"]' and remove "root['" or 'root["' prefix
                if path.startswith("root['"):
                    end_quote = path.find("']")
                    prefix_len = 6  # "root['"
                else:  # root[""
                    end_quote = path.find('"]')
                    prefix_len = 6  # 'root["'

                if end_quote > prefix_len:
                    field_name = path[prefix_len:end_quote]
                    remaining = path[end_quote+2:]  # Everything after "']" or '"]'
                    return field_name + remaining
            elif path.startswith("root[") and path.endswith("]"):
                # Handle cases like root[0] -> 0
                return path[5:-1]  # Remove "root[" and "]"
            elif path.startswith("root."):
                return path[5:]  # Remove "root."
            else:
                # Fallback: remove "root" prefix
                return path[4:] if path.startswith("root") else path
        else:
            return path

    @staticmethod
    def _normalize_repo_url(url: str) -> str:
        """Normalize repository URL to ignore trivial differences."""
        if not url:
            return url

        # Remove trailing slash first
        if url.endswith('/'):
            url = url[:-1]

        # Remove trailing .git if present
        if url.endswith('.git'):
            url = url[:-4]

        return url

    @staticmethod
    def _repos_are_equivalent(repo1: str, repo2: str) -> bool:
        """Check if two repository URLs are equivalent (ignoring trivial differences)."""
        # Handle None/empty cases - treat None and empty string as equivalent
        if (repo1 is None or repo1 == "") and (repo2 is None or repo2 == ""):
            return True
        if repo1 is None or repo1 == "" or repo2 is None or repo2 == "":
            return False

        return YamlComparer._normalize_repo_url(repo1) == YamlComparer._normalize_repo_url(repo2)

    @staticmethod
    def _find_unique_items_with_equivalence(items1: set, items2: set, equivalence_func=None) -> tuple[set, set]:
        """Find items unique to each set, using optional equivalence function.

        Args:
            items1: First set of items
            items2: Second set of items
            equivalence_func: Function to check equivalence between items (optional)

        Returns:
            Tuple of (only_in_1, only_in_2) sets
        """
        if equivalence_func is None:
            # Simple set difference
            return items1 - items2, items2 - items1

        # Use equivalence function
        only_in_1 = set()
        only_in_2 = set()

        # Find items only in items1
        for item1 in items1:
            found_equivalent = False
            for item2 in items2:
                if equivalence_func(item1, item2):
                    found_equivalent = True
                    break
            if not found_equivalent:
                only_in_1.add(item1)

        # Find items only in items2
        for item2 in items2:
            found_equivalent = False
            for item1 in items1:
                if equivalence_func(item1, item2):
                    found_equivalent = True
                    break
            if not found_equivalent:
                only_in_2.add(item2)

        return only_in_1, only_in_2

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

    def _compare_items(self, taqasta_items: List[Dict[str, Any]],
                      canasta_items: List[Dict[str, Any]],
                      item_type: str,
                      show_details_for_unique: bool = True,
                      compare_repos_and_branches: bool = True) -> str:
        """Generic method to compare items (extensions or skins) between Taqasta and Canasta.

        Args:
            taqasta_items: List of item dicts from Taqasta
            canasta_items: List of item dicts from Canasta
            item_type: String like "Extensions" or "Skins"
            show_details_for_unique: Whether to show commit/repo details for unique items
            compare_repos_and_branches: Whether to compare repos/branches for common items
        """
        output = []

        # Convert both lists to dicts for easier comparison
        taqasta_item_dict = {item: data for item_list in taqasta_items
                            for item, data in item_list.items()}
        canasta_item_dict = {item: data for item_list in canasta_items
                            for item, data in item_list.items()}

        taqasta_names = set(taqasta_item_dict.keys())
        canasta_names = set(canasta_item_dict.keys())

        # Items only in Taqasta
        only_taqasta = taqasta_names - canasta_names
        if only_taqasta:
            output.append(f"  {item_type} only in Taqasta:")
            for item in sorted(only_taqasta):
                output.append(f"    + {item}")
                if show_details_for_unique:
                    # Show key details
                    item_data = taqasta_item_dict[item]
                    if 'commit' in item_data:
                        output.append(f"        commit: {item_data['commit']}")
                    if 'repository' in item_data:
                        output.append(f"        repository: {item_data['repository']}")

        # Items only in Canasta
        only_canasta = canasta_names - taqasta_names
        if only_canasta:
            output.append(f"  {item_type} only in Canasta:")
            for item in sorted(only_canasta):
                output.append(f"    - {item}")
                if show_details_for_unique:
                    # Show key details
                    item_data = canasta_item_dict[item]
                    if 'commit' in item_data:
                        output.append(f"        commit: {item_data['commit']}")
                    if 'repository' in item_data:
                        output.append(f"        repository: {item_data['repository']}")

        # Items in both - compare details
        common = taqasta_names & canasta_names
        if common:
            differences = []
            for item in sorted(common):
                taqasta_data = taqasta_item_dict[item]
                canasta_data = canasta_item_dict[item]

                diff = DeepDiff(taqasta_data, canasta_data, ignore_order=True)
                if diff:
                    # Check if there are any meaningful differences (not just equivalent repositories)
                    has_meaningful_differences = False

                    # Check specific fields first
                    taqasta_commit = taqasta_data.get('commit')
                    canasta_commit = canasta_data.get('commit')

                    if compare_repos_and_branches:
                        taqasta_repo = taqasta_data.get('repository')
                        canasta_repo = canasta_data.get('repository')
                        taqasta_branch = taqasta_data.get('branch')
                        canasta_branch = canasta_data.get('branch')
                        taqasta_steps = set(taqasta_data.get('additional steps', []))
                        canasta_steps = set(canasta_data.get('additional steps', []))

                        if any([
                            taqasta_commit != canasta_commit,
                            not self._repos_are_equivalent(taqasta_repo, canasta_repo),
                            taqasta_branch != canasta_branch,
                            taqasta_steps != canasta_steps
                        ]):
                            has_meaningful_differences = True
                    else:
                        # For skins, just compare commits
                        if taqasta_commit != canasta_commit:
                            has_meaningful_differences = True

                    # Check DeepDiff for other meaningful differences
                    if not has_meaningful_differences:
                        for change_type, changes in diff.items():
                            if change_type == 'values_changed':
                                for path, change in changes.items():
                                    clean_path = self._clean_diff_path(path)
                                    old_val = change.get('old_value', 'None')
                                    new_val = change.get('new_value', 'None')

                                    # Skip repository differences that are equivalent
                                    if compare_repos_and_branches and clean_path == 'repository' and self._repos_are_equivalent(old_val, new_val):
                                        continue

                                    has_meaningful_differences = True
                                    break
                                if has_meaningful_differences:
                                    break
                            elif change_type in ['type_changes', 'dictionary_item_added', 'dictionary_item_removed',
                                               'iterable_item_added', 'iterable_item_removed']:
                                # These are always meaningful differences
                                has_meaningful_differences = True
                                break

                    # Only add to differences if there are meaningful differences
                    if has_meaningful_differences:
                        differences.append((item, taqasta_data, canasta_data, diff))

            if differences:
                output.append(f"  {item_type} with different configurations:")
                for item, taqasta_data, canasta_data, diff in differences:
                    output.append(f"    ~ {item}:")

                    # Compare commits
                    taqasta_commit = taqasta_data.get('commit')
                    canasta_commit = canasta_data.get('commit')
                    if taqasta_commit != canasta_commit:
                        output.append(f"        Taqasta commit: {taqasta_commit}")
                        output.append(f"        Canasta commit: {canasta_commit}")

                    if compare_repos_and_branches:
                        # Compare repositories
                        taqasta_repo = taqasta_data.get('repository')
                        canasta_repo = canasta_data.get('repository')
                        if not self._repos_are_equivalent(taqasta_repo, canasta_repo):
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
                    other_differences = []
                    for change_type, changes in diff.items():
                        if change_type == 'values_changed':
                            for path, change in changes.items():
                                clean_path = self._clean_diff_path(path)
                                old_val = change.get('old_value', 'None')
                                new_val = change.get('new_value', 'None')

                                # Skip fields that are already handled explicitly
                                if clean_path == 'commit':
                                    continue  # Commit differences are shown separately
                                if compare_repos_and_branches and clean_path == 'repository':
                                    continue  # Repository differences are shown separately
                                if compare_repos_and_branches and clean_path == 'branch':
                                    continue  # Branch differences are shown separately
                                if compare_repos_and_branches and clean_path == 'additional steps':
                                    continue  # Additional steps differences are shown separately

                                other_differences.append(f"          {clean_path}: '{old_val}' → '{new_val}'")
                        elif change_type == 'type_changes':
                            for path, change in changes.items():
                                clean_path = self._clean_diff_path(path)
                                old_type = change.get('old_type', 'Unknown')
                                new_type = change.get('new_type', 'Unknown')
                                other_differences.append(f"          {clean_path}: type changed from {old_type} to {new_type}")
                        elif change_type == 'dictionary_item_added':
                            for path in changes:
                                clean_path = self._clean_diff_path(path)
                                other_differences.append(f"          Added: {clean_path}")
                        elif change_type == 'dictionary_item_removed':
                            for path in changes:
                                clean_path = self._clean_diff_path(path)
                                other_differences.append(f"          Removed: {clean_path}")
                        elif change_type == 'iterable_item_added':
                            other_differences.append(f"          Added {len(changes)} item(s) to iterable")
                        elif change_type == 'iterable_item_removed':
                            other_differences.append(f"          Removed {len(changes)} item(s) from iterable")

                    # Only show "Other differences" if there are actual differences to show
                    if other_differences:
                        output.append(f"        Other differences:")
                        output.extend(other_differences)

        return "\n".join(output) if output else ""

    def _compare_extensions(self, taqasta_exts: List[Dict[str, Any]],
                           canasta_exts: List[Dict[str, Any]]) -> str:
        """Compare extensions between Taqasta and Canasta."""
        return self._compare_items(taqasta_exts, canasta_exts, "Extensions", show_details_for_unique=True, compare_repos_and_branches=True)

    def _compare_skins(self, taqasta_skins: List[Dict[str, Any]],
                      canasta_skins: List[Dict[str, Any]]) -> str:
        """Compare skins between Taqasta and Canasta."""
        return self._compare_items(taqasta_skins, canasta_skins, "Skins", show_details_for_unique=False, compare_repos_and_branches=False)

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

        # Compare using equivalence check
        only_taqasta, only_canasta = self._find_unique_items_with_equivalence(
            taqasta_repo_urls, canasta_repo_urls, self._repos_are_equivalent
        )

        if only_taqasta:
            output.append("  Custom repositories only in Taqasta:")
            for repo in sorted(only_taqasta):
                output.append(f"    + {repo}")

        if only_canasta:
            output.append("  Custom repositories only in Canasta:")
            for repo in sorted(only_canasta):
                output.append(f"    - {repo}")

        return "\n".join(output) if output else ""
