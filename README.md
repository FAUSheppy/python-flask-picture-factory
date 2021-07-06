# python-flask picture factory
This server provides and caches images based on url-arguments.

# Ussage
Place your images in the "/pictures/"-subdirectory.

    ../pictures
        ├── picture1.png
        ├── picture2.jpg
        ├── picture3

Run the server, either as:

    python ./server

or:

    /usr/bin/waitress-serve --host 127.0.0.1 --port 5002 --call 'app:createApp'*

Retrive the images with these URLs:

    http://server:port/media/picture1.png?x=100&y=200&encoding=webp
    http://server:port/media/picture2.jpg?x=100
    http://server:port/media/picture3.jpg?y=200&encoding=png

You may omitt any of the parameters. Not giving any parameters will return the original image. You must always name the original picture in your URL, even if you want a different encoding.

# Other possible URL-parameters:
In addition to *encoding*, *scaleX* and *scaleY* you may also use the following parameters:

    force=True/False -> apply the x/y-values as given, cut off image when necessary
    cacheTimeout=SECONDS -> add a cache timeout header witht the given value to the response

# Futher explanation
I wrote a small article with some more example on how to best use this to optimize your website -if you want to use it for that: [Medium](https://medium.com/anti-clickbait-coalition/responsive-image-factory-f1ed6e61d13c)
