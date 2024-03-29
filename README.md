# python-flask picture factory
This server provides and caches images based on url-arguments.

# Usage
Place your images in the "/pictures/"-subdirectory.

    ../pictures
        ├── picture1.png
        ├── picture2.jpg
        ├── picture3

Run the server, either as:

    python ./server

or:

    /usr/bin/waitress-serve --host 127.0.0.1 --port 5002 --call 'app:createApp'*

Retrieve the images with these URLs:

    http://server:port/media/picture1.png?x=100&y=200&encoding=webp
    http://server:port/media/picture2.jpg?x=100
    http://server:port/media/picture3.jpg?y=200&encoding=png

You may omit any of the parameters. Not giving any parameters will return the original image. You must always name the original picture in your URL, even if you want a different encoding.

# Other possible URL-parameters:
In addition to *encoding*, *scaleX* and *scaleY* you may also use the following parameters:

    force=True/False -> apply the x/y-values as given, cut off image when necessary
    cacheTimeout=SECONDS -> add a cache timeout header with the given value to the response

# Uploading
This tool is not intended for uploading or large amounts of files, use SFTP/FTPS or whatever your server provides for. For pure convenience usage there is a */upload*/-location. It must be enabled by creating a file called *upload.enable* in the project root before the server is started.

For automatic redirection after upload you must have a reverse proxy setting a header *X-REAL-HOSTNAME* with the internet facing hostname of the server.

# With nginx as reverse-proxy

    server {
        listen 443 ssl;
        location /{
            proxy_pass http://localhost:5000;
        }

        location /upload{
            auth_basic "Auth Message";
            auth_basic_user_file "/path/to/auth/file";
            client_max_body_size 50m; # <-- important!
            proxy_set_header X-REAL-HOSTNAME $host;
            proxy_pass http://localhost:5000;
        }
    }

# With Docker-Compose

    version: '3'
    services:
        image-factory:
        image: atlantis-image-factory
        restart: always
        ports:
            - "5000:5000"
        environment:
            UPLOAD_ENABLED: yes
            PICTURES_DIRECTORY: picture
        volumes:
            - "/data/image-factory/pictures/:/app/pictures/"

# Further explanation
I wrote a small article with some more example on how to best use this to optimize your website -if you want to use it for that: [Medium](https://medium.com/anti-clickbait-coalition/responsive-image-factory-f1ed6e61d13c)
