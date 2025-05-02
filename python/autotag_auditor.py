import boto3
import argparse

# Define required tags that should be present
REQUIRED_TAGS = ["Owner", "Environment", "CostCenter"]

# Apply missing tags to an EC2 instance
def tag_ec2(ec2, instance_id, missing_tags):
    ec2.create_tags(Resources=[instance_id], Tags=missing_tags)

# Apply missing tags to an S3 bucket
def tag_s3(s3, bucket_name, missing_tags):
    # S3 requires full tag overwrite, so we must fetch existing tags first
    try:
        existing = s3.get_bucket_tagging(Bucket=bucket_name)["TagSet"]
    except s3.exceptions.ClientError:
        existing = []
    except Exception:
        existing = []

    # Combine existing and missing tags (no duplicates)
    all_tags = {tag["Key"]: tag["Value"] for tag in existing}
    for tag in missing_tags:
        all_tags[tag["Key"]] = tag["Value"]

    new_tagset = [{"Key": k, "Value": v} for k, v in all_tags.items()]
    s3.put_bucket_tagging(Bucket=bucket_name, Tagging={"TagSet": new_tagset})

# Evaluate tags and apply if needed
def check_and_fix_tags(resource_type, identifier, tags, boto_client, auto_tags, dry_run):
    tag_dict = {tag['Key']: tag['Value'] for tag in tags} if tags else {}
    missing_keys = [key for key in REQUIRED_TAGS if key not in tag_dict]

    if not missing_keys:
        print(f"{resource_type} {identifier} is compliant.")
        return

    print(f"{resource_type} {identifier} is missing tags: {', '.join(missing_keys)}")

    if auto_tags and not dry_run:
        # Build missing tags from user-supplied defaults
        missing_tag_objs = [{"Key": k, "Value": auto_tags[k]} for k in missing_keys if k in auto_tags]
        if missing_tag_objs:
            if resource_type == "EC2":
                tag_ec2(boto_client, identifier, missing_tag_objs)
            elif resource_type == "S3":
                tag_s3(boto_client, identifier, missing_tag_objs)
            print(f"🔧 Applied missing tags to {resource_type} {identifier}: {missing_tag_objs}")

# Scan EC2 instances
def audit_ec2(auto_tags, dry_run):
    ec2 = boto3.client("ec2")
    try:
        reservations = ec2.describe_instances()["Reservations"]
    except Exception as e:
        print(f"EC2 API error: {e}")
        return

    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            tags = instance.get("Tags", [])
            check_and_fix_tags("EC2", instance_id, tags, ec2, auto_tags, dry_run)

# Scan S3 buckets
def audit_s3(auto_tags, dry_run):
    s3 = boto3.client("s3")
    try:
        buckets = s3.list_buckets()["Buckets"]
    except Exception as e:
        print(f"S3 API error: {e}")
        return

    for bucket in buckets:
        name = bucket["Name"]
        try:
            tagging = s3.get_bucket_tagging(Bucket=name)
            tags = tagging["TagSet"]
        except s3.exceptions.ClientError:
            tags = []
        except Exception:
            tags = []

        check_and_fix_tags("S3", name, tags, s3, auto_tags, dry_run)

# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tag audit and auto-fix for EC2 + S3")
    parser.add_argument("--dry-run", action="store_true", help="Only simulate tagging, make no changes")
    parser.add_argument("--auto-tag", nargs="+", help="Provide default tags to apply (e.g., Owner=YourName)")

    args = parser.parse_args()

    # Parse --auto-tag into dictionary
    default_tags = {}
    if args.auto_tag:
        for pair in args.auto_tag:
            if "=" in pair:
                key, val = pair.split("=", 1)
                default_tags[key] = val

    print("\nAuditing EC2...")
    audit_ec2(default_tags, args.dry_run)

    print("\nAuditing S3...")
    audit_s3(default_tags, args.dry_run)
