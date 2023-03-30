import os
import datetime
import uuid
from flask import Flask, request, send_from_directory, make_response, jsonify
from werkzeug.utils import secure_filename

def create_app(test_config=None):
    
    app = Flask(__name__, static_folder='../build', static_url_path='/')

    secret_key_value = uuid.uuid4().hex

    app.config.from_mapping(
        SECRET_KEY = secret_key_value,
        DATABASE = os.path.join(app.instance_path,'denoise.sqlite'),
        UPLOAD_FOLDER = os.path.join(app.instance_path,'uploads'),
        RESULT_FOLDER = os.path.join(app.instance_path,'results'),
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'},
        MAX_CONTENT_LENGTH = 1024 * 1024
    )

    try:
        os.makedirs(app.instance_path)
        os.mkdir(app.config['UPLOAD_FOLDER'])
        os.mkdir(app.config['RESULT_FOLDER'])
    except OSError:
        pass

    #### start pytorch model
    import json
    import torch
    from torchvision.utils import save_image
    from app.model.net import CDLNet
    from app.model.utils import img_load
    from app.model.nle import noise_level

    # torch.set_num_threads(1)
    args_file = open(os.path.join('trained_net/args.json'))
    args = json.load(args_file)
    model = CDLNet(**args['model'],init=False)
    print("Model initiated",flush=True)
    ckpt = torch.load(os.path.join('trained_net/net.ckpt'), map_location=torch.device('cpu'))
    model.load_state_dict(ckpt['net_state_dict'])
    print("Model loaded",flush=True)
    model.eval()
    model.share_memory()
    for param in model.parameters():
        param.grad = None

    ### start databse
    with app.app_context():
        from app.db import get_db, init_db
        init_db()
    

    def predict(file):
        image = img_load(file)
        print("Loaded Image",flush=True)
        if(image.shape[1]==4):
            image = image[:,0:3,:,:]
        
        sigma = 255 * noise_level(image, method='MAD')
        print("Sigma is ",torch.flatten(sigma),flush=True)
        with torch.no_grad():
            image_p = model(image,sigma)
        # print("Finished",flush=True)
        # for (i, xz) in enumerate(fg):
        #     continue
        # image_p = xz
        return image_p

    def allowed_file(filename):
        return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    # @app.route('/upload', methods=['POST'])
    # def upload():
    #     if 'file' not in request.files:
    #         return ('No file part', 400)
    #     file = request.files['file']
    #     if file.filename == '':
    #         return ('No file selected', 400)
    #     if not allowed_file(file.filename):
    #         return ('Wrong file type', 400)
        
    #     db = get_db()

    #     filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + '.png'

    #     try:
    #         db.execute(
    #             "INSERT INTO files (filename,status) VALUES (?,?)",
    #             (filename, 1),
    #         )
    #         db.commit()
    #     except db.IntegrityError:
    #         pass

    #     file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))

    #     resp = make_response('',204)
    #     resp.set_cookie('filename',filename)
    #     # session['filename'] = filename
    #     print(filename,flush=True)

    #     return resp
    
    @app.route('/process', methods=['POST'])
    def result():

        resp = make_response()
        if 'file' not in request.files:
            resp.headers['error'] = 'No file part'
            return resp
        request_file = request.files['file']
        if request_file.filename == '':
            resp.headers['error'] = 'No file selected'
            return resp
        if not allowed_file(request_file.filename):
            resp.headers['error'] = 'Wrong file type'
            return resp

        filename = request.cookies.get('timestamp') + '.png'
        db = get_db()

        file = db.execute(
            'SELECT * FROM files WHERE filename = ?', (filename,)
        ).fetchone()

        if file is not None:
            resp.headers['error'] = 'File is being processed'
            return resp

        db.execute(
                "INSERT INTO files (filename,status) VALUES (?,?)",
                (filename, 1),
        )
        db.commit()

        request_file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))

        image_p = predict(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        save_image(image_p,os.path.join(app.instance_path,app.config['RESULT_FOLDER'],'p_'+filename))

        resp = make_response(send_from_directory(app.config['RESULT_FOLDER'], 'p_'+filename))
        resp.headers['error'] = 'OK'
        return resp

    @app.route('/delete')
    def delete_image():

        filename = request.cookies.get('timestamp') + '.png'

        if not os.path.isfile(os.path.join(app.instance_path,app.config['UPLOAD_FOLDER'],filename)):
            return ('File does not exist',400)
        os.remove(os.path.join(app.instance_path,app.config['UPLOAD_FOLDER'],filename))

        if not os.path.isfile(os.path.join(app.instance_path,app.config['RESULT_FOLDER'],'p_'+filename)):
            return ('File does not exist',400)
        os.remove(os.path.join(app.instance_path,app.config['RESULT_FOLDER'],'p_'+filename))
        
        db = get_db()
        db.execute('DELETE FROM files WHERE filename = ?', (filename,))
        db.commit()

        return ('',204)
    
    @app.route('/')
    def index():

        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        resp = make_response(app.send_static_file('index.html'))
        resp.set_cookie('timestamp',timestamp)
        return resp

    return app