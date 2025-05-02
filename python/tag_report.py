import boto3
import csv

# List of services and resource types to check
REQUIRED_TAG_KEYS = ["Owner", "Environment", "CostCenter"]

# Export all tags from EC2 instances
def export_ec2_tags():
    ec2 = boto3.client("ec2")
    output = []

    # Describe all EC2 instances in all reservations
    reservations = ec2.describe_instances()["Reservations"]
    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            tags = instance.get("Tags", [])
            tag_dict = {tag["Key"]: tag["Value"] for tag in tags} if tags else {}

            # Build output row
            row = {
                "ResourceType": "EC2",
                "ResourceId": instance_id,
                "Owner": tag_dict.get("Owner", ""),
                "Environment": tag_dict.get("Environment", ""),
                "CostCenter": tag_dict.get("CostCenter", "")
            }
            output.append(row)

    return output

# Export all tags from S3 buckets
def export_s3_tags():
    s3 = boto3.client("s3")
    output = []

    try:
        buckets = s3.list_buckets()["Buckets"]
    except Exception as e:
        print(f"Failed to list S3 buckets: {e}")
        return output

    for bucket in buckets:
        bucket_name = bucket["Name"]
        tag_dict = {}

        try:
            # Try to get tags for this bucket
            tagging = s3.get_bucket_tagging(Bucket=bucket_name)
            tag_dict = {tag["Key"]: tag["Value"] for tag in tagging["TagSet"]}
        except s3.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchTagSet':
                # Bucket exists but has no tags
                tag_dict = {}
            else:
                print(f"Error reading tags for bucket {bucket_name}: {e}")
                continue
        except Exception as e:
            print(f"Unexpected error with bucket {bucket_name}: {e}")
            continue

        row = {
            "ResourceType": "S3",
            "ResourceId": bucket_name,
            "Owner": tag_dict.get("Owner", ""),
            "Environment": tag_dict.get("Environment", ""),
            "CostCenter": tag_dict.get("CostCenter", "")
        }
        output.append(row)

    return output


# Write all rows to a CSV file
def write_csv(filename, rows):
    headers = ["ResourceType", "ResourceId", "Owner", "Environment", "CostCenter"]

    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Exported {len(rows)} records to {filename}")

# Entry point
if __name__ == "__main__":
    # Run audits
    ec2_data = export_ec2_tags()
    s3_data = export_s3_tags()

    # Combine both outputs and write to CSV
    all_data = ec2_data + s3_data
    write_csv("tag_report.csv", all_data)
