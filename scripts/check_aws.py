"""Read-only AWS connection checks; never prints credential values."""
import argparse
import json
import sys

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, MissingDependencyException


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="stateguard")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--expected-account", default="299335570672")
    args = parser.parse_args()
    config = Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 1})
    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        identity = session.client("sts", config=config).get_caller_identity()
        account = identity["Account"]
        print(json.dumps({"profile": args.profile, "region": args.region, "account": account,
                          "expected_account_matches": account == args.expected_account}))
        if account != args.expected_account:
            print("Wrong account selected. Stop before accessing project resources.")
            return 2
        try:
            response = session.client("bedrock", config=config).get_foundation_model(
                modelIdentifier="amazon.nova-micro-v1:0")
            print(json.dumps({"bedrock_metadata_access": True,
                              "model": response["modelDetails"]["modelId"],
                              "note": "Metadata access does not prove permission to invoke the model."}))
        except ClientError as exc:
            print(json.dumps({"bedrock_metadata_access": False, "error_code": exc.response["Error"]["Code"]}))
            return 3
        try:
            quota = session.client("service-quotas", config=config).get_service_quota(
                ServiceCode="bedrock", QuotaCode="L-D2912E70")["Quota"]
            print(json.dumps({"nova_micro_daily_token_allowance": quota["Value"],
                              "note": "Allowance, not tokens consumed or remaining."}))
            if quota["Value"] <= 0:
                print("AWS authentication works, but Nova Micro has zero inference allowance. AWS Support case 178912681900290 is pending; repeated model calls will not fix this.")
                return 4
        except ClientError as exc:
            print(json.dumps({"quota_check": "unavailable", "error_code": exc.response["Error"]["Code"],
                              "note": "Quota inspection is not required for inference; model invocation remains unverified."}))
        return 0
    except ClientError as exc:
        print(json.dumps({"connected": False, "error_code": exc.response["Error"]["Code"]}))
    except MissingDependencyException:
        print(json.dumps({"connected": False, "error_type": "MissingDependencyException",
                          "next_step": "Install the SDK login dependency: python -m pip install -e .[aws-login]"}))
    except BotoCoreError as exc:
        print(json.dumps({"connected": False, "error_type": type(exc).__name__,
                          "next_step": "Complete AWS CLI login and verify the selected profile."}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
