#!/usr/bin/env python3
import sys
import os
from math import ceil


def split_csv(input_file, num_chunks=4):
    """Split a CSV file into even chunks while preserving complete rows."""

    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    # Get base filename without extension
    base_name = os.path.splitext(input_file)[0]
    extension = os.path.splitext(input_file)[1]

    print(f"Reading file: {input_file}")

    # Read the file and clean NUL bytes
    try:
        with open(input_file, 'rb') as f:
            content = f.read()

        # Remove NUL bytes
        if b'\x00' in content:
            print("Warning: NUL bytes detected in file. Cleaning...")
            content = content.replace(b'\x00', b'')

        # Convert to text
        text_content = content.decode('utf-8', errors='ignore')

        # Split into lines
        lines = text_content.strip().split('\n')

    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    total_lines = len(lines)

    if total_lines == 0:
        print("Error: File is empty")
        sys.exit(1)

    # Simple header detection
    first_line = lines[0]
    # Check if first line might be a header (contains letters or common header patterns)
    has_header = any(char.isalpha() for char in first_line) or 'id' in first_line.lower()

    if has_header:
        header = lines[0]
        data_lines = lines[1:]
        total_data_lines = len(data_lines)
    else:
        header = None
        data_lines = lines
        total_data_lines = total_lines

    # Calculate lines per chunk
    lines_per_chunk = ceil(total_data_lines / num_chunks)

    print(f"Total lines: {total_lines}")
    if has_header:
        print(f"Header detected: {header[:100]}..." if len(header) > 100 else f"Header detected: {header}")
        print(f"Data lines: {total_data_lines}")
    print(f"Lines per chunk: {lines_per_chunk}")
    print(f"Creating {num_chunks} files...")
    print()

    # Split and write chunks
    files_created = []
    for i in range(num_chunks):
        start_idx = i * lines_per_chunk
        end_idx = min((i + 1) * lines_per_chunk, total_data_lines)

        # Skip if no data for this chunk
        if start_idx >= total_data_lines:
            continue

        # Create output filename
        output_file = f"{base_name}_part{i + 1}{extension}"

        # Write chunk
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header if exists
                if has_header:
                    f.write(header + '\n')

                # Write data lines for this chunk
                for line in data_lines[start_idx:end_idx]:
                    f.write(line + '\n')

            actual_lines = end_idx - start_idx
            total_written = actual_lines + (1 if has_header else 0)
            print(f"Created {output_file} with {total_written} lines " +
                  f"({actual_lines} data rows" + (", 1 header row)" if has_header else ")"))
            files_created.append(output_file)

        except Exception as e:
            print(f"Error writing {output_file}: {e}")

    print(f"\nSuccessfully created {len(files_created)} files")


def split_csv_alternative(input_file, num_chunks=4):
    """Alternative method using binary mode throughout"""

    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    # Get base filename without extension
    base_name = os.path.splitext(input_file)[0]
    extension = os.path.splitext(input_file)[1]

    print(f"Reading file (alternative method): {input_file}")

    # Read file in binary mode and filter NUL bytes line by line
    lines = []
    with open(input_file, 'rb') as f:
        for line in f:
            # Remove NUL bytes from each line
            cleaned_line = line.replace(b'\x00', b'')
            # Decode and strip line endings
            try:
                decoded_line = cleaned_line.decode('utf-8', errors='ignore').rstrip('\r\n')
                if decoded_line:  # Skip empty lines
                    lines.append(decoded_line)
            except:
                continue

    if not lines:
        print("Error: No valid lines found in file")
        sys.exit(1)

    total_lines = len(lines)

    # Continue with same logic as before...
    # [Rest of the function would be the same as above]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_csv.py <input_file.csv>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Expand home directory if needed
    input_file = os.path.expanduser(input_file)

    split_csv(input_file)