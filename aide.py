import os
import shutil
import subprocess
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask import Response, stream_with_context
from werkzeug.middleware.proxy_fix import ProxyFix
from ansi2html import Ansi2HTMLConverter

conv = Ansi2HTMLConverter(inline=True)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for Android WebView

# main.py এর একদম শুরুতে (import এর পরে)
CURRENT_EDITOR_PATH = None
HOME_DIR = os.path.expanduser("~/")
WORKSPACE_DIR = os.path.join(HOME_DIR, "workspace")
TEMPLATE_PROJECT_DIR = os.path.join(HOME_DIR, "AIDE", "MyApplication")
TEMPLATE_PACKAGE = "com.example.myapplication"
RUNAPK_CMD = os.path.expanduser("~/bin/runapk")  # Termux executable path

if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

# ==================== Helper Functions ====================

def replace_in_file(file_path, old_text, new_text):
    try:
        if os.path.isfile(file_path):
            normalized_path = file_path.replace("\\", "/")
            # Skip mipmap folders, .gradle folders/files, and kls_database.db
            if ("/mipmap" in normalized_path or
                "/.gradle" in normalized_path or
                os.path.basename(file_path) == "kls_database.db"):
                return
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content_new = content.replace(old_text, new_text)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content_new)
    except Exception as e:
        print(f"Error replacing in {file_path}: {e}")

def rename_package_dirs(base_path, old_pkg, new_pkg):
    old_path = os.path.join(base_path, *old_pkg.split('.'))
    new_path = os.path.join(base_path, *new_pkg.split('.'))
    if os.path.exists(old_path):
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.move(old_path, new_path)
        cleanup_empty_dirs(os.path.join(base_path, old_pkg.split('.')[0]))
        return new_path

def cleanup_empty_dirs(path):
    if os.path.isdir(path) and not os.listdir(path):
        os.rmdir(path)
        parent = os.path.dirname(path)
        cleanup_empty_dirs(parent)

def update_all_files(project_path, old_pkg, new_pkg, project_name):
    for root, dirs, files in os.walk(project_path):
        for file in files:
            file_path = os.path.join(root, file)
            replace_in_file(file_path, old_pkg, new_pkg)
            replace_in_file(file_path, "MyApplication", project_name)

# ==================== Routes ====================

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/create_project', methods=['GET','POST'])
def create_project():
    if request.method == 'GET':
        return render_template("createProject.html")
    
    data = request.get_json(force=True)
    app_name = data.get('app_name', '').strip()
    package_name = data.get('package_name', '').strip()
    min_sdk = data.get('min_sdk')
    
    if not app_name or not package_name:
        return jsonify({"status":"error","message":"Project name and package required"})
    
    new_project_path = os.path.join(WORKSPACE_DIR, app_name)
    if os.path.exists(new_project_path):
        return jsonify({"status":"error","message":"Project already exists"})
    
    # Copy template project
    shutil.copytree(TEMPLATE_PROJECT_DIR, new_project_path)
    
    # Rename package directories
    base_java_path = os.path.join(new_project_path, "app", "src", "main", "java")
    rename_package_dirs(base_java_path, TEMPLATE_PACKAGE, package_name)
    
    base_test_path = os.path.join(new_project_path, "app", "src", "test", "java")
    rename_package_dirs(base_test_path, TEMPLATE_PACKAGE, package_name)
    
    base_android_test_path = os.path.join(new_project_path, "app", "src", "androidTest", "java")
    rename_package_dirs(base_android_test_path, TEMPLATE_PACKAGE, package_name)
    
    # Update package names and project name in all files
    update_all_files(new_project_path, TEMPLATE_PACKAGE, package_name, app_name)
    
    # Streaming Gradle wrapper output
    def generate():
        yield f"Project '{app_name}' created at {new_project_path}\n\n"
        gradle_cmd = ["gradle", "wrapper", "--gradle-version", "9.0.0"]
        try:
            process = subprocess.Popen(
                gradle_cmd,
                cwd=new_project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            line_num = 0
            for line in iter(process.stdout.readline, ''):
                line_num += 1
                # সিরিয়াল নাম্বার prepend করা হচ্ছে
                numbered_line = f"{line_num:>4}: {line.rstrip()}"
                yield f"{numbered_line}\n\n"
                #yield line

            process.stdout.close()
            process.wait()
            yield "\nGradle wrapper finished.\n"
        except Exception as e:
            yield f"\nGradle wrapper failed: {e}\n"

            
    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/open_project')
def open_project():
    items = []
    if os.path.exists(WORKSPACE_DIR):
        try:
            file_list = sorted(os.listdir(WORKSPACE_DIR))
            for f in file_list:
                full_path = os.path.join(WORKSPACE_DIR, f)
                items.append({
                    "name": f,
                    "path": full_path,
                    "is_dir": os.path.isdir(full_path)
                })
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        except OSError:
            items = []
    
    return render_template("openProject.html", items=items)

@app.route("/delete_item", methods=["POST"])
def delete_item():
    data = request.get_json()
    if not data or "path" not in data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    path = data.get("path")
    if not path or not os.path.abspath(path).startswith(os.path.abspath(WORKSPACE_DIR)):
        return jsonify({"status": "error", "message": "Unauthorized path"}), 403

    if not os.path.exists(path):
        return jsonify({"status": "error", "message": "Item not found"}), 404

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return jsonify({"status": "ok", "message": "Item deleted successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

#==================================
@app.route('/set_editor_path', methods=['POST'])
def set_editor_path():
    global CURRENT_EDITOR_PATH
    data = request.json
    filepath = data.get('path')

    if not filepath:
        return jsonify({'status': 'error', 'message': 'No path provided'})

    abs_path = os.path.join(WORKSPACE_DIR, filepath)

    if not os.path.exists(abs_path):
        return jsonify({'status': 'error', 'message': 'File/Folder not found'})

    # ✅ গ্লোবাল ভ্যারিয়েবলে সেট করো
    CURRENT_EDITOR_PATH = abs_path
    return jsonify({'status': 'ok'})

@app.route('/editor')
def ide():
    return render_template('editor.html')

# ✅ নতুন API - Files list (Fixed)
@app.route('/api/files')
def list_files():
    try:
        # ✅ এখন থেকে সব লিস্ট CURRENT_EDITOR_PATH এর ভেতর থেকে হবে
        base_dir = CURRENT_EDITOR_PATH if CURRENT_EDITOR_PATH else WORKSPACE_DIR

        files = []
        if not os.path.exists(base_dir):
            return jsonify([])

        for root, dirs, filenames in os.walk(base_dir):
            for file in filenames:
                if any(file.endswith(ext) for ext in ['.kt', '.java', '.xml', '.gradle', '.txt']):
                    full_path = os.path.relpath(os.path.join(root, file), base_dir)
                    files.append(full_path)

        return jsonify({'files': files, 'base': os.path.basename(base_dir)})
    except Exception as e:
        return jsonify({'error': str(e)})

# ✅ নতুন API - Get file content (Fixed)
@app.route('/api/files/<path:filename>')
def get_file(filename):
    try:
        base_dir = CURRENT_EDITOR_PATH if CURRENT_EDITOR_PATH else WORKSPACE_DIR
        filepath = os.path.join(base_dir, filename)

        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'})

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)})

# ✅ নতুন API - Save file (Fixed)
@app.route('/api/save', methods=['POST'])
def save_file():
    try:
        data = request.json

        # ✅ এখন থেকে CURRENT_EDITOR_PATH বেইস হিসেবে ধরবে
        base_dir = CURRENT_EDITOR_PATH if CURRENT_EDITOR_PATH else WORKSPACE_DIR
        filepath = os.path.join(base_dir, data['filepath'])
        code = data['code']
        
        # ✅ Directory create করুন যদি না থাকে
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/run', methods=['POST'])
def install_apk():
    try:
        data = request.json
        # ✅ Find APK file
        base_dir = CURRENT_EDITOR_PATH if CURRENT_EDITOR_PATH else WORKSPACE_DIR
        apk_path = os.path.join(base_dir, 'app/build/outputs/apk/debug/app-debug.apk')
        
        if os.path.exists(apk_path):
            # ✅ Install APK
            result = subprocess.run(
                ['termux-open', apk_path],
                capture_output=True,
                text=True
            )
            return jsonify({
                'message': 'APK installed successfully',
                'output': result.stdout,
                'error': result.stderr
            })
        else:
            return jsonify({'error': 'APK not found. Build the project first.'})
    except Exception as e:
        return jsonify({'error': str(e)})


#=================================


@app.route("/run_project")
def run_project():
    project_path = request.args.get("path")

    if not project_path or not os.path.abspath(project_path).startswith(os.path.abspath(WORKSPACE_DIR)) or not os.path.isdir(project_path):
        return Response("Invalid or unauthorized project path", status=400)

    def generate_output():
        try:
            process = subprocess.Popen(
                [RUNAPK_CMD],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            line_num = 0  # সিরিয়াল নাম্বার কাউন্টার

            for line in iter(process.stdout.readline, ""):
                line_num += 1
                # সিরিয়াল নাম্বার prepend করা হচ্ছে
                numbered_line = f"\033[1;32m{line_num:>4}:\033[0m {line.rstrip()}"
                html_line = conv.convert(numbered_line, full=False)
                yield f"data: {html_line}\n\n"

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                yield f"data: {conv.convert('✅ Build completed successfully! 🎉', full=False)}\n\n"
            else:
                yield f"data: {conv.convert(f'❌ Build failed with exit code {return_code}', full=False)}\n\n"

        except FileNotFoundError:
            yield f"data: {conv.convert(f'❌ Error: The command {RUNAPK_CMD} was not found.', full=False)}\n\n"
        except Exception as e:
            yield f"data: {conv.convert(f'❌ Error: {str(e)}', full=False)}\n\n"

        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate_output()), mimetype="text/event-stream")


@app.route('/git_clone', methods=['GET','POST'])
def git_clone():
    if request.method == 'GET':
        return render_template("gitClone.html")
    
    data = request.get_json(force=True)
    url = data.get('repo_url')
    if not url:
        return jsonify({"status":"error","message":"Repository URL required"})
    
    try:
        repo_name = os.path.basename(url).replace('.git', '')
        target_dir = os.path.join(WORKSPACE_DIR, repo_name)
        subprocess.run(["git", "clone", url, target_dir], check=True, capture_output=True, text=True)
        return jsonify({"status":"ok","message":"Repository cloned successfully"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status":"error","message": f"Git error: {e.stderr}"})
    except Exception as e:
        return jsonify({"status":"error","message": str(e)})

# ==================== Run App ====================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)




