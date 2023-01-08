#!/usr/bin/python3
import os
import flask
import argparse
import sys
import PIL.Image
import werkzeug.utils
import flask_oidc
import json

app = flask.Flask("Picture factory app", static_folder=None)

## OIDC CONFIG SETUP ##
if os.path.isfile("oidc.json"):
    with open("oidc.json") as f:
        app.config |= json.load(f)
    if not os.path.isfile("client_secrets.json"):
        raise ValueError("client_secrets.json file is missing in project root")
else:
    raise ValueError("OIDC required by environment but not oidc.json file found")

oidc = flask_oidc.OpenIDConnect(app)
PICTURE_DIR = "pictures/"

def generatePicture(pathToOrig, scaleX, scaleY, encoding, crop):
    '''Generate an pictures with the requested scales and encoding if it doesn't already exist'''

    CACHE_DIR = os.path.join("cache/")

    if os.path.isfile(CACHE_DIR):
        raise OSError("Picture cache dir is occupied by a file!")
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    filename, extension = os.path.splitext(os.path.basename(pathToOrig))
    if not encoding:
        encoding = extension.strip(".")

    # just python things... #
    if encoding.lower() == "jpg":
        encoding = "jpeg"

    # open image #
    try:
        image = PIL.Image.open(os.path.join(PICTURE_DIR, pathToOrig))
    except FileNotFoundError:
        return (None, False)

    # ensure sizes are valid #
    x, y = image.size
    if not scaleY:
        scaleY = y
    if not scaleX:
        scaleX = x

    scaleX = min(x, scaleX)
    scaleY = min(y, scaleY)

    # generate new paths #
    newFile = "x-{x}-y-{y}-{fname}.{ext}".format(x=scaleX, y=scaleY, fname=filename, ext=encoding)
    newPath = os.path.join(CACHE_DIR, newFile)

    # check for cache
    print(newPath)
    if os.path.isfile(newPath):
        return (newPath, True)

    # save image with new size and encoding #
    if image.mode in ("RGBA", "P") and encoding in ("jpeg"):
        image = image.convert("RGB")

    if crop:
        image.crop((0, 0, scaleX, scaleY))
        print(scaleX, scaleY)
    else:
        print("scale")
        image.thumbnail((scaleX, scaleY), PIL.Image.ANTIALIAS)

    image.save(newPath, encoding)

    # strip the STATIC_DIR because we will use send_from_directory for safety #
    REPLACE_ONCE = 1
    return (newPath.replace(PICTURE_DIR, "", REPLACE_ONCE), False)

@app.route("/media/<path:path>")
@app.route("/m/<path:path>")
@app.route("/picture/<path:path>")
@app.route("/pictures/<path:path>")
@app.route("/image/<path:path>")
@app.route("/images/<path:path>")
def sendPicture(path):
    cache_timeout = 2592000

    y1 = flask.request.args.get("scaley")
    x1 = flask.request.args.get("scalex")
    y2 = flask.request.args.get("y")
    x2 = flask.request.args.get("x")

    # check variables #
    scaleY, scaleX = (None, None)
    if y1:
        scaleY = round(float(y1))
    elif y2:
        scaleY = round(float(y2))

    if x1:
        scaleX = round(float(x1))
    elif x2:
        scaleX = round(float(x2))

    pathDebug = path
    if path.endswith(".svg"):
        return flask.send_from_directory(".", path)

    encoding = flask.request.args.get("encoding")
    path, cacheHit = generatePicture(path, scaleX, scaleY, encoding,
                            bool(flask.request.args.get("crop")))
    if not path:
        return ("File not found: {}".format(os.path.join(PICTURE_DIR, pathDebug)), 404)

    raw = flask.send_from_directory(".", path, cache_timeout=cache_timeout)
    response = flask.make_response(raw)

    response.headers['X-PICTURE-FACTORY-INTERNAL-FID'] = path
    response.headers['X-PICTURE-FACTORY-INTERNAL-CACHE-HIT'] = cacheHit

    # check for a cacheTimeout #
    cacheTimeout = flask.request.args.get("cache-timeout")
    if not cacheTimeout:
        cacheTimeout = flask.request.args.get("ct")
    if cacheTimeout:
        response.headers['Cache-Control'] = "max-age=" + str(cacheTimeout)
    else:
        response.headers['Cache-Control'] = "max-age=" + "3600"

    if encoding:
        response.headers['Content-Type'] = "image/{}".format(encoding)

    return response

@app.route("/")
def list():
    retStringArr = []
    for root, dirs, files in os.walk(PICTURE_DIR):
        path = root.split(os.sep)
        for f in files:
            retStringArr += [os.path.join(os.path.basename(root), f)]

    return flask.render_template("index.html", paths=retStringArr)

@app.route("/upload", methods = ['GET', 'POST'])
@oidc.require_login
def upload():
    if not app.config['UPLOAD_ENABLED']:
        return ("Upload Disabled", 403)
    if flask.request.method == 'POST':
        f = flask.request.files['file']
        fname = werkzeug.utils.secure_filename(f.filename)
        sfName = os.path.join(PICTURE_DIR, fname)
        if not os.path.isfile(sfName):
            f.save(sfName)
            realHostname = flask.request.headers.get("X-REAL-HOSTNAME")
            if realHostname:
                return flask.redirect("/media/" + fname)
            else:
                return ('Success', 204)
        else:
            return ('Conflicting File', 409)
    else:
        return flask.render_template("upload.html")

@app.before_first_request
def init():
    app.config['MAX_CONTENT_PATH'] = 32+1000*1000
    app.config['UPLOAD_FOLDER']    = PICTURE_DIR
    app.config['UPLOAD_ENABLED']   = os.path.isfile("./upload.enable")
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Picture Factory',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # general parameters #
    parser.add_argument("-i", "--interface", default="127.0.0.1", help="Interface to listen on")
    parser.add_argument("-p", "--port",      default="5000",      help="Port to listen on")

    # startup #
    args = parser.parse_args()
    app.run(host=args.interface, port=args.port)
