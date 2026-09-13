# AWS connection diagnosis — September 11, 2026

Account: 299335570672. Region: us-east-1. Local profile: stateguard.

Fixed locally: AWS CLI installation; browser login; Python console-login dependency (`botocore[crt]`). STS verified the expected account. Bedrock GetFoundationModel succeeded for `amazon.nova-micro-v1:0`.

Live Converse and ConverseStream requests returned `ThrottlingException`: “Too many tokens per day, please wait before trying again.” Service Quotas reported:

| Quota | Code | Applied value | Adjustable via Service Quotas |
|---|---|---:|---|
| Nova Micro model invocation tokens per day | L-D2912E70 | 0 | No |
| Nova Micro on-demand tokens per minute | L-CFA4FA0D | 0 | No |
| Nova Micro on-demand requests per minute | L-E118F160 | 0 | No |
| Nova Micro cross-region tokens per minute | L-DC7FF66C | 0 | Yes |
| Nova Micro cross-region requests per minute | L-3F110E0F | 0 | No |

The zero daily allowance is not an expired login or a transient per-minute burst. Additional checks confirmed an ACTIVE PAID account plan, authorized model access, and zero daily quotas across multiple models in us-east-1 and us-west-2. These establish the blocker but do not reveal AWS's internal reason for the zero allocation.

A request for 10,000 cross-region tokens/minute was rejected because the quota-increase API required a value above its stated default of 8,000,000, despite the applied quota being zero. No quota increase was accepted, and no paid capacity or support upgrade was purchased.

## Submitted support case

The user submitted account support case **178912681900290**, subject **bedrock model connectin**, on September 11, 2026 at 11:40:19 UTC. Category: Service Quotas, General. Status verified in the console: **Work in progress**. The submitted correspondence contains the account/region/model checks, failed small quota request, zero allowances, and hackathon deadline. No AWS response was visible when checked. Do not resolve or duplicate this case while awaiting the account/quota review.

## Original support draft (superseded by the submitted case)

Subject: Enable Amazon Bedrock Nova Micro inference — applied account quotas are zero

Our account 299335570672 is building StateGuard for the Agents for Humans hackathon. In us-east-1, authenticated STS and Bedrock model metadata requests work, but Amazon Nova Micro inference fails with “Too many tokens per day” even for a four-output-token test.

Service Quotas reports the Nova Micro daily invocation-token quota (L-D2912E70), on-demand TPM (L-CFA4FA0D), and on-demand RPM (L-E118F160) as zero and not adjustable. Please explain any activation or account restriction and enable a small development allowance suitable for bounded Strands investigations, each limited to six agent turns and 4,000 output tokens. Please advise the minimum available quota and any account verification needed. We do not require provisioned throughput.

## After AWS enables inference

Run `python scripts/check_aws.py` to verify the session; metadata access alone is not an inference test. If the session expired, run `aws login --profile stateguard --region us-east-1`.

Install the persistent Python dependency with `python -m pip install -e ".[aws-login]"`. Stop the existing local API before launching `./scripts/start-local.ps1 -Live`. The launcher uses the signed-in profile and stores a separate local demo-access key in the git-ignored `.stateguard-live-key` file. This key is not an AWS credential. Configure a dedicated limited-permission AWS identity before any production deployment; the session used for this diagnosis was the account root identity.

The app now disables Strands' long automatic model retry loop and returns an explicit HTTP 429 for model throttling. No successful live agent run has been claimed or recorded.
