import argparse
import yaml

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c", "--input-config",
        type=str,
        required=True,
        action="store",
        help="Set config.yml",
        dest="config_path"
    )
    parser.add_argument(
        "-k", "--keys",
        type=str,
        required=True,
        nargs="*",
        action="store",
        help="Set keys",
        dest="keys"
    )
    args = parser.parse_args()
    
    with open(args.config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    result = config
    for k in args.keys:
        result = result[k]
    print(result, end='')

if __name__ == "__main__":
    # execute only if run as a script
    main()
