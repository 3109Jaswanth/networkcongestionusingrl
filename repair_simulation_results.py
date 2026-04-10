import argparse
import json
import re
from pathlib import Path


def try_load_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def repair_truncated_json(text: str) -> str | None:
    # Common truncation pattern: ends while writing an array/object.
    # For this project, the JSON often truncates inside the final MADQN time_series actions array.
    match = re.search(r'\s*"actions"\s*:\s*\[\s*$', text)
    if not match:
        return None

    prefix = text[:match.start()]
    prefix = re.sub(r',\s*$', '', prefix)

    candidate = prefix + '''
                  }
              ]
          ,
          "queue_history": [],
          "actions": []
      }
}
'''

    if try_load_json(candidate) is not None:
        return candidate

    candidate = prefix + '''
                  }
              ]
          }
}
'''
    if try_load_json(candidate) is not None:
        return candidate

    return None


def main():
    parser = argparse.ArgumentParser(description='Repair a truncated simulation JSON result file.')
    parser.add_argument('input', type=Path, help='Path to malformed JSON result file')
    parser.add_argument('--output', type=Path, help='Output path for repaired JSON file')
    args = parser.parse_args()

    input_path = args.input
    if not input_path.exists():
        raise FileNotFoundError(f'Missing input file: {input_path}')

    text = input_path.read_text()
    valid = try_load_json(text)
    if valid is not None:
        print(f'Input file is already valid JSON: {input_path}')
        return

    repaired = repair_truncated_json(text)
    if repaired is None:
        raise ValueError('Could not automatically repair the malformed JSON file.')

    output_path = args.output or input_path.with_suffix(input_path.suffix + '.repaired.json')
    output_path.write_text(repaired)
    print(f'Repaired JSON written to: {output_path}')


if __name__ == '__main__':
    main()
