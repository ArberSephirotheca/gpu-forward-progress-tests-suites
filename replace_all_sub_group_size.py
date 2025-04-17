import re
from pathlib import Path

def replace_and_copy(src_file, src_root, dst_root):
    relative_path = src_file.relative_to(src_root)
    dst_file = dst_root / relative_path

    # Create parent directories if needed
    dst_file.parent.mkdir(parents=True, exist_ok=True)

    with src_file.open('r') as f:
        lines = f.readlines()

    pattern = re.compile(r'^\s*uint\s+subgroup_size\s*=\s*gl_SubgroupSize\s*;\s*$')
    modified_lines = []

    for line in lines:
        if pattern.match(line):
            modified_lines.append("uint subgroup_size = 16;\n")
        else:
            modified_lines.append(line)

    with dst_file.open('w') as f:
        f.writelines(modified_lines)

    print(f"📄 Written: {dst_file}")

def main():
    src_root = Path('./all_tests')
    dst_root = Path('./all_tests_fixed_subgroup')

    for comp_file in src_root.rglob('*.comp'):
        replace_and_copy(comp_file, src_root, dst_root)

if __name__ == '__main__':
    main()
