import boto3
import os
import argparse

REQUIRED_TAGS = ["Owner", "Environment", "CostCenter"]

def check_tags(resource_type, identifier, tags):
    tag_dict = {tag['Key']: tag['Value'] for tag in tags} if tags else {}
    missing = [t for t in REQUIRED_TAGS if t not in tag_dict]
    if missing:
        print(f"{resource_type} {identifier} is missing tags: {', '.join(missing)}")
    else:
        print(f"{resource_type} {identifier} has all required tags.")

def audit_ec2(dry_run=False):
    ec2 = boto3.client("ec2")
    try:
        instances = ec2.describe_instances()
    except Exception as e:
        print(f"Failed to list EC2 instances: {e}")
        return

    for reservation in instances.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instance_id = instance["InstanceId"]
            tags = instance.get("Tags", [])
            if dry_run:
                print(f"[DRY-RUN] EC2 instance {instance_id} would be checked for tags.")
            else:
                check_tags("EC2", instance_id, tags)

def audit_s3(dry_run=False):
    s3 = boto3.client("s3")
    try:
        buckets = s3.list_buckets()["Buckets"]
    except Exception as e:
        print(f"Failed to list S3 buckets: {e}")
        return

    for bucket in buckets:
        name = bucket["Name"]
        if dry_run:
            print(f"[DRY-RUN] S3 bucket {name} would be checked for tags.")
            continue

        try:
            tagging = s3.get_bucket_tagging(Bucket=name)
            tags = tagging["TagSet"]
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                tags = []
            else:
                print(f"Error retrieving tags for bucket {name}: {e}")
                continue
        except Exception as e:
            print(f"Unexpected error for bucket {name}: {e}")
            continue

        check_tags("S3", name, tags)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AWS tag compliance auditor for EC2 and S3")
    parser.add_argument("--dry-run", action="store_true", help="Simulate checks without accessing tags")
    args = parser.parse_args()

    print("Checking EC2 instances...")
    audit_ec2(dry_run=args.dry_run)

    print("\nChecking S3 buckets...")
    audit_s3(dry_run=args.dry_run)
