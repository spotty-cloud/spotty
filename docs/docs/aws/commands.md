---
layout: default
title: Commands
parent: AWS Provider
nav_order: 2
permalink: /docs/aws-provider/commands/
---

# AWS Commands

Commands that are specific for an AWS provider:

  - `spotty aws create-ami [-h] [-d] [-c CONFIG] [--debug-mode] [INSTANCE_NAME]`

    Creates an AMI with NVIDIA Docker. An AMI should be created only once for an AWS region.

  - `spotty aws delete-ami [-h] [-d] [-c CONFIG] [INSTANCE_NAME]`

    Deletes an AMI that was created using the `spotty aws create-ami` command.

  - `spotty aws spot-prices [-h] [-d] -i INSTANCE_TYPE [-r REGION]`

    Returns Spot Instance prices for a particular instance type across all AWS regions or within a specific region.
