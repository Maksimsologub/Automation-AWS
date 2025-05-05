# Automation-AWS

A practical collection of Infrastructure-as-Code (IaC) scripts using **Terraform** and **Python** to automate AWS infrastructure provisioning, auditing, tagging, and backups.

---

## 📁 Folder Structure

```bash
aws-infra-lab/
├── python/                  # Python scripts for automation and auditing
│   ├── iam_audit.py         # Audit IAM users for MFA and activity
│   ├── tag_auditor.py       # Generate tag compliance report
│   ├── autotag_auditor.py   # Auto-apply missing tags (optional dry-run)
│   ├── tag_report.csv       # Output: tag compliance report
│   ├── ec2_snapshot_backup.py # Daily EC2 snapshot with optional pruning
│   ├── run_daily_backup.sh  # Scheduled cron job for EC2 backup
│   └── README.md            # Python-specific usage
│
├── terraform/               # Terraform IaC for deploying AWS resources
│   ├── main.tf              # EC2 and S3 infrastructure config
│   └── .gitignore           # Ignores .terraform/ and *.tfstate for safety
