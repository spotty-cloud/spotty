---
layout: default
title: Commands
parent: AWS
nav_order: 2
permalink: /docs/aws/commands/
---

# AWS Commands

Available commands:

  - `$ spotty aws create-ami`

    Creates an AMI with NVIDIA Docker. An AMI should be created only once for an AWS region.

  - `$ spotty aws delete-ami [-r AWS_REGION]`

    Deletes an AMI that was created using the `spotty aws create-ami` command.

  - `$ spotty aws spot-prices -i INSTANCE_TYPE [-r AWS_REGION]`

    Returns Spot Instance prices for particular instance type across all AWS regions or within a specific region.
