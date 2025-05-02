# Import AWS SDK for Python
import boto3

# Import date/time tools to calculate how old keys are or when users last logged in
from datetime import datetime, timezone, timedelta

# Define the threshold in days for considering a user or key "stale"
DAYS_THRESHOLD = 90

# Check if a user has MFA enabled
def check_mfa(iam, user):
    # Returns a list of MFA devices attached to the user
    mfa = iam.list_mfa_devices(UserName=user)
    # If there is at least one device, MFA is enabled
    return len(mfa['MFADevices']) > 0

# Check access keys for the user and return any that are older than the threshold
def check_access_keys(iam, user):
    keys = iam.list_access_keys(UserName=user)['AccessKeyMetadata']
    flagged = []  # Holds any keys that are too old
    for key in keys:
        # Calculate key age
        age = (datetime.now(timezone.utc) - key['CreateDate']).days
        if age > DAYS_THRESHOLD:
            # Append any old key with its age to the list
            flagged.append((key['AccessKeyId'], age))
    return flagged

# Main function that runs the full audit
def main():
    # Create a client to talk to AWS IAM
    iam = boto3.client('iam')
    try:
        # Get a list of all IAM users in the account
        users = iam.list_users()['Users']
    except Exception as e:
        # Handle any permission or API issues gracefully
        print(f"Failed to fetch IAM users: {e}")
        return

    print("\nIAM User Security Audit Report")
    print("-" * 40)

    # Loop over every IAM user
    for user in users:
        name = user['UserName']
        print(f"\nChecking user: {name}")

        flags = []  # List to hold findings for this user

        # Check when they last logged in
        login_time = user.get('PasswordLastUsed')
        if login_time:
            # How many days since last login?
            days_since = (datetime.now(timezone.utc) - login_time).days
            if days_since > DAYS_THRESHOLD:
                flags.append(f"Last login: {days_since} days ago")
        else:
            flags.append("Never logged in")

        # Check for MFA
        if not check_mfa(iam, name):
            flags.append("No MFA")

        # Check access key age
        keys = check_access_keys(iam, name)
        for k, age in keys:
            flags.append(f"Access key {k} is {age} days old")

        # Output audit results
        if flags:
            for f in flags:
                print(f)
        else:
            print("Compliant")

# Run the main function only if this file is executed directly
if __name__ == "__main__":
    main()
