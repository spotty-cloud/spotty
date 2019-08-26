---
layout: default
title: Account Preparation
parent: GCP Provider (beta)
nav_order: 1
permalink: /docs/gcp-provider/account-preparation/
---

# Account Preparation

1. [Create a project](https://console.cloud.google.com/projectcreate){:target="_blank"} 
if you don't have one already.
2. Enable the [Deployment Manager API](https://console.cloud.google.com/apis/library/deploymentmanager.googleapis.com){:target="_blank"} 
for the created project.
3. Enable the [Runtime Configuration API](https://console.developers.google.com/apis/library/runtimeconfig.googleapis.com){:target="_blank"} 
for the created project.
4. [Create a service account](https://console.cloud.google.com/iam-admin/serviceaccounts/create){:target="_blank"}.
5. Add the __"Compute Admin"__, __"Deployment Manager Editor"__ and __"Cloud RuntimeConfig Admin"__ 
roles to the created service account: [https://console.cloud.google.com/iam-admin/iam](https://console.cloud.google.com/iam-admin/iam){:target="_blank"}.
6. Make sure you have a quota to run GPU instances:
    1. Go to the quotas page in "IAM & admin" and filter the list of services by setting the Metric 
    field to __"GPUs (all regions)"__: [https://console.cloud.google.com/iam-admin/quotas?metric=GPUs%20(all%20regions)](https://console.cloud.google.com/iam-admin/quotas?metric=GPUs%20(all%20regions)){:target="_blank"}.
    2. Check the limit for the __"Compute Engine API"__ service. If it's a zero, select the service and 
    click the __"[+] EDIT QUOTAS"__ button at the top of the page.
    3. Set a new quota limit to 1 or more and submit the request.
7. [Install Google Cloud SDK](https://cloud.google.com/sdk/install){:target="_blank"}.
8. Before using Spotty commands like `spotty start`, `spotty run` and others, make sure that the 
`GOOGLE_APPLICATION_CREDENTIALS` environmental variable is set up and contains the path to your service 
account key file:
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/the/service/account/key/file.json"
    ```
