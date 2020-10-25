# Caching Docker Image on an EBS Volume

You can cache images that you've built or downloaded from the internet on an EBS volume or in a snapshot.

A configuration file has the "__dockerDataRoot__" parameter. It's a directory on the host OS where the Docker 
daemon will save all the images.

Specify the `moundDir` directory for one of the instance volumes and set the `dockerDataRoot` parameter
to the same value (or to a subdirectory of the `moundDir` directory). Also, consider changing a deletion policy
for that volume to "__retain__", then the volume with the cache will be retained and the next time it just will be 
attached to the instance.

Example:
```yaml
# ...

instances:
  - name: aws-1
    provider: aws
    parameters:
      # ...
      dockerDataRoot: /docker
      volumes:
        # ...
        - name: docker
          parameters:
            size: 10
            mountDir: /docker
```
