from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_WORKFLOW = ROOT / ".github" / "workflows" / "pangram-paid-dispatch.yml"

# This high-risk registration boundary is deliberately snapshot-locked. Any
# trigger, permission, job, context, action, secret, or command change requires
# an explicit policy-test update and review.
EXPECTED_REGISTRATION_WORKFLOW = """name: Pangram paid dispatcher registration

on:
  workflow_dispatch:
    inputs:
      spec_path:
        description: Repository-relative fixed-batch JSON under experiments/
        required: true
        type: string
      result_path:
        description: Optional canonical state/experiments result path
        required: false
        default: ''
        type: string
      paid_run_confirmation:
        description: Select the evidence branch before explicitly acknowledging paid credits
        required: true
        default: DO_NOT_RUN
        type: choice
        options:
          - DO_NOT_RUN
          - RUN_PAID_PANGRAM_FIXED_BATCH

permissions: {}

jobs:
  refuse-default-branch:
    runs-on: ubuntu-latest
    timeout-minutes: 2
    steps:
      - name: Require the canonical evidence branch
        shell: bash
        run: |
          echo "::error::This default-branch file only registers the manual route. Select automation/pangram-fixed-batch in the Branch menu."
          exit 1
"""


def test_default_branch_registration_is_exactly_fail_closed() -> None:
    assert (
        REGISTRATION_WORKFLOW.read_text(encoding="utf-8")
        == EXPECTED_REGISTRATION_WORKFLOW
    )
