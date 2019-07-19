---
layout: default
title: Commands
parent: GCP Provider
nav_order: 2
permalink: /docs/gcp-provider/commands/
---

# GCP Commands

Available commands:

  - `spotty gcp create-image [-h] [-d] [-c CONFIG] [-f FAMILY_NAME] [--debug-mode] [INSTANCE_NAME]`

    Creates an image with NVIDIA Docker.

  - `spotty gcp delete-image [-h] [-d] [-c CONFIG] [INSTANCE_NAME]`

    Deletes an image that was created using the `spotty gcp create-image` command.
