import json
import os
import argparse
import boto3
import logging
from pathlib import Path
import glob
import yaml

logger = logging.getLogger(__name__)

def create_s3(stack_name: str):
    bucket_name = stack_name + '-' + os.environ['CODEBUILD_BUILD_ID'].replace(':', '-').replace('/', '-')
    logger.debug('Create s3 bucket: ' + bucket_name)
    s3 = boto3.resource('s3', region_name=boto3.session.Session().region_name)
    bucket = s3.Bucket(bucket_name)
    bucket.create(CreateBucketConfiguration={'LocationConstraint': boto3.session.Session().region_name})
    return bucket_name

def upload_file_to_s3(bucket_name: str, filepath_list: list, root_path: str):
    s3 = boto3.resource('s3', region_name=boto3.session.Session().region_name)
    root_path_str = str(Path(root_path).resolve())
    for f in filepath_list:
        logger.debug('Upload s3 bucket: ' + f)
        f_str = str(Path(f).resolve())
        s3.Object(bucket_name, f_str.replace(root_path_str, '')[1:]).upload_file(f)

def get_public_url(bucket, target_object_path):
    s3 = boto3.client('s3', region_name=boto3.session.Session().region_name)
    bucket_location = s3.get_bucket_location(Bucket=bucket)
    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        bucket_location['LocationConstraint'],
        bucket,
        target_object_path)

def find_cfn_files(base_folder_path: str):
    filepath_list = []
    filepath_list.extend(list(glob.glob(os.path.join(base_folder_path + "/**/*.json"), recursive=True)))
    filepath_list.extend(list(glob.glob(os.path.join(base_folder_path + "/**/*.yml"), recursive=True)))
    filepath_list.extend(list(glob.glob(os.path.join(base_folder_path + "/**/*.yaml"), recursive=True)))
    filepath_list.extend(list(glob.glob(os.path.join(base_folder_path + "/**/*.template"), recursive=True)))
    return filepath_list

def upload_cfn(bucket_name:str, input_path: str):
    
    filepath_list = find_cfn_files(str(Path(input_path).parent))
    upload_file_to_s3(bucket_name, filepath_list, str(Path(input_path).parent))
    return get_public_url(bucket_name, Path(input_path).name), bucket_name


def load_parameter_file(param_path: str):
    root, ext = os.path.splitext(param_path)
    content = ''
    with open(param_path, encoding='utf-8') as f:
        content = f.read()
    if ext == '.json':
        result = json.loads(content)
    else:
        result = yaml.safe_load(content)
    return result

def generate_parameter(param_path: str, s3_bucket_url_parameter_key_name: str, bucket_name: str):
    param = load_parameter_file(param_path)

    result = []
    if isinstance(param, list):
        if len(list(filter(lambda p: 'ParameterKey' in p and 'ParameterValue' in p, param))) == len(param):
            result = param
        else:
            raise('Not support parameter file')
    elif isinstance(param, dict):
        result = []
        for k, v in param.items():
            if isinstance(v, dict) or isinstance(v, list):
                raise('Not support parameter file')
            result.append({
                'ParameterKey': k,
                'ParameterValue': v
            })
    else:
        raise('Not support parameter file')
    if s3_bucket_url_parameter_key_name != None:
        for r in list(filter(lambda p: p['ParameterKey'] == s3_bucket_url_parameter_key_name, result)):
            r['ParameterValue'] = 'https://{}.s3.amazonaws.com'.format(bucket_name)
    return result

def create_taskcat_file(config: dict, param_list: list):
    config['taskcat']['template'] = config['template']

    param = {}
    for p in param_list:
        param[p['ParameterKey']] = p['ParameterValue']
    taskcat_dict = {
        'project': {
            'name': config['name']
        },
        'tests': {
            config['name']: {
                'template': config['template'],
                'parameters': param,
                'regions': config['taskcat']['regions']
            }
        }
    }
    with open('./.taskcat.yml', 'w', encoding='utf-8') as f:
        yaml.dump(taskcat_dict, f)

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
        "-s3", "--s3-bucket-url-parameter-key-name",
        type=str,
        action="store",
        dest="s3_bucket_url_parameter_key_name",
        help="Set the parameter key name to this, if the input path is a local file and you want to reflect the S3 bucket name to be uploaded in the parameter."
    )
    parser.add_argument(
        "-V", "--verbose",
        action='store_true',
        dest="detail",
        help="give more detailed output"
    )
    args = parser.parse_args()

    if args.detail:
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        logger.info('Set detail log level.')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        
    logger.info('Initialize to codebuild')
    
    with open(args.config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    bucket_name = create_s3(config['name'])
    config['created']['bucket_name'] = bucket_name
    filepath_list = find_cfn_files(str(Path(config['template']).parent))
    for filepath in filepath_list:
        upload_cfn(bucket_name, filepath)
    param_list = generate_parameter(config['parameter'], args.s3_bucket_url_parameter_key_name, bucket_name)
    create_taskcat_file(config, param_list)

    logger.info('Successfully to initialize')

if __name__ == "__main__":
    # execute only if run as a script
    main()
