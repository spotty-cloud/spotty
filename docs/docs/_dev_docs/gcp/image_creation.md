# Creating a Public Spotty Image

1. Create an image.

    Example of `spotty.yaml`:
    ```yaml
    # ...
    
    instances:
      - name: gcp-image
        provider: gcp
        parameters:
          zone: us-central1-a
          machineType: n1-standard-1
          onDemandInstance: true
          imageName: spotty-image-[x-x-x]-[YYYYMMDD]
          gpu:
            type: nvidia-tesla-k80
    ```
   
    The `imageName` parameter should contain a version of the image from the 
    `spotty.providers.gcp.deployment.image_deployment.ImageDeployment.VERSION` property.

    If new image is incompatible with the current version of Spotty, the family name should be
    changed to `spotty_<version>`, where the `<version>` (written with dashes) is a version of Spotty 
    since new image will be supported. The family name should also be changed in the code with the next release (
   `spotty/providers/gcp/deployment/instance_deployment.py`, `_get_image()` method).

    A command to create an image:
    ```bash
    spotty gcp create-image -f spotty-1-2-5
    ```

2. Share a created image:
    
    - Get the image policy:
    
        ```bash
        IMAGE_NAME=spotty-1-0-0-20190827
        gcloud compute images get-iam-policy $IMAGE_NAME --format json > policy.json
        ```
    
    - Update the `policy.json` file by adding `bindings`:

        ```json
        {
          "etag": "ACAB",
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
