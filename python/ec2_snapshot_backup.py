import boto3
from datetime import datetime, timezone, timedelta
import argparse

# Create a snapshot for the given volume with tags
def create_snapshot(ec2, volume_id, description, tags):
    try:
        snapshot = ec2.create_snapshot(
            VolumeId=volume_id,
            Description=description,
            TagSpecifications=[{
                'ResourceType': 'snapshot',
                'Tags': tags
            }]
        )
        print(f"Created snapshot {snapshot['SnapshotId']} for volume {volume_id}")
    except Exception as e:
        print(f"Failed to create snapshot for {volume_id}: {e}")

# Delete snapshots older than N days that were created by automation
def prune_old_snapshots(ec2, retention_days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']

    for snap in snapshots:
        tags = {tag['Key']: tag['Value'] for tag in snap.get('Tags', [])}
        if tags.get('CreatedBy') == 'Automation':
            if snap['StartTime'] < cutoff:
                sid = snap['SnapshotId']
                try:
                    ec2.delete_snapshot(SnapshotId=sid)
                    print(f"🗑 Deleted old snapshot {sid} (older than {retention_days} days)")
                except Exception as e:
                    print(f"Failed to delete snapshot {sid}: {e}")

# Main snapshot logic
def backup_volumes(retention_days=7, prune=False):
    ec2 = boto3.client('ec2')

    try:
        reservations = ec2.describe_instances(Filters=[
            {"Name": "instance-state-name", "Values": ["running"]}
        ])["Reservations"]
    except Exception as e:
        print(f"Could not fetch EC2 instances: {e}")
        return

    for res in reservations:
        for instance in res["Instances"]:
            instance_id = instance["InstanceId"]
            for mapping in instance.get("BlockDeviceMappings", []):
                volume_id = mapping["Ebs"]["VolumeId"]

                timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
                description = f"Backup {volume_id} from {instance_id} at {timestamp}"

                tags = [
                    {"Key": "CreatedBy", "Value": "Automation"},
                    {"Key": "Project", "Value": "InfraBackup"},
                    {"Key": "Timestamp", "Value": timestamp}
                ]

                create_snapshot(ec2, volume_id, description, tags)

    if prune:
        prune_old_snapshots(ec2, retention_days)

# CLI entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🔁 EC2 Volume Snapshot Automation")
    parser.add_argument("--retention", type=int, default=7, help="Delete snapshots older than this (days)")
    parser.add_argument("--prune", action="store_true", help="Enable pruning of old snapshots")
    args = parser.parse_args()

    backup_volumes(retention_days=args.retention, prune=args.prune)
