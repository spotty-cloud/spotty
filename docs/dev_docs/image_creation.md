# Creating a Public Spotty Image

1. Create an image.

    Example of `spotty.yaml`:
    ```yaml
    # ...
    
    instances:
      - name: i1
        provider: gcp
        parameters:
          zone: us-central1-a
          machineType: n1-standard-1
          onDemandInstance: true
          imageName: spotty-1-0-0-20190827
          gpu:
            type: nvidia-tesla-k80
    ```
    
    A command to create an image:
    ```bash
    spotty gcp create-image -f spotty
    ```

2. Share a created image:
    
    - Get the image policy:
    
        ```bash
        IMAGE_NAME=spotty-1-0-0-20190827
        gcloud compute images get-iam-policy $IMAGE_NAME --format json > policy.json
        ```
    
    - Update the `policy.json` file:

        ```json
        {
          "etag": "BwWRHwABAg0=",
          "version": 1,
          "bindings": [
            {
              "members": [
                "allAuthenticatedUsers"
              ],
              "role": "roles/compute.imageUser"
            }
          ]
        }
        ```
    
    - Set a new policy for the image:
    
        ```bash
        gcloud compute images set-iam-policy $IMAGE_NAME policy.json
        ```

    Read more [here](https://cloud.google.com/compute/docs/access/granting-access-to-resources#sharing_specific_images_with_the_public).
