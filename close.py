import argparse
import boto3
import logging
import yaml

logger = logging.getLogger(__name__)

def delete_bucket(bucket_name, dryrun=False):
    contents_count = 0
    next_token = ''
    client = boto3.client('s3')

    while True:
        if next_token == '':
            response = client.list_objects_v2(Bucket=bucket_name)
        else:
            response = client.list_objects_v2(Bucket=bucket_name, ContinuationToken=next_token)

        if 'Contents' in response:
            contents = response['Contents']
            contents_count = contents_count + len(contents)
            for content in contents:
                if not dryrun:
                    logger.debug("Deleting: s3://" + bucket_name + "/" + content['Key'])
                    client.delete_object(Bucket=bucket_name, Key=content['Key'])
                else:
                    logger.debug("DryRun: s3://" + bucket_name + "/" + content['Key'])

        if 'NextContinuationToken' in response:
            next_token = response['NextContinuationToken']
        else:
            break
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    bucket.delete()

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
        
    logger.info('Close to codebuild')
    
    with open(args.config_path, 'r') as f:
        config = yaml.safe_load(f)

    delete_bucket(config['created']['bucket_name'])

    logger.info('Successfully to close')

if __name__ == "__main__":
    # execute only if run as a script
    main()
