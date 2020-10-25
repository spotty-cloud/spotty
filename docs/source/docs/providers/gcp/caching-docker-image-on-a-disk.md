# Caching Docker Image on a Disk

You can cache images that you've built or downloaded from the internet on a disk that you attach to the instance.

A configuration file has the "__dockerDataRoot__" parameter. It's a directory on the host OS where the Docker 
daemon will save all the images.

Specify the `moundDir` directory for one of the instance volumes and set the `dockerDataRoot` parameter
to the same value (or to a subdirectory of the `moundDir` directory).

Example:
```yaml
# ...

instances:
  - name: gcp-1
    provider: gcp
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
